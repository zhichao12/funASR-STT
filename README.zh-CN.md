# FunASR STT 服务

这是给 ESP32 板子使用的本地语音转文字服务。服务提供 HTTP 接口，ESP32 可以把录音上传到电脑或 VPS 上运行的 FunASR，再拿到识别文本。

## 一键启动

```bash
docker compose up -d --build
```

Windows 也可以运行：

```powershell
.\run.ps1
```

默认地址：

```text
http://127.0.0.1:10095
```

如果给 ESP32 使用，请把固件里的 `APP_AI_STT_BASE_URL` 改成运行 Docker 的电脑局域网 IP，例如：

```text
http://192.168.1.23:10095
```

## ESP32 使用检查清单

1. 启动服务：

```powershell
.\run.ps1
```

2. 先在电脑本机确认服务健康：

```powershell
Invoke-RestMethod http://127.0.0.1:10095/health
```

3. 找到电脑局域网 IP，例如 `192.168.1.2`，再用和 ESP32 同一网络里的手机或另一台设备测试：

```text
http://192.168.1.2:10095/health
```

4. 如果局域网 `10095` 能打开，固件里配置：

```c
#define APP_AI_STT_BASE_URL "http://192.168.1.2:10095"
```

5. 如果电脑本机能打开 `10095`，但局域网打不开，就启动 Windows 辅助代理：

```powershell
python funasr_proxy_10096.py
```

再测试：

```text
http://192.168.1.2:10096/health
```

固件里配置：

```c
#define APP_AI_STT_BASE_URL "http://192.168.1.2:10096"
```

## 接口

- `GET /health`
- `POST /asr`
- `POST /asr_base64`

## 环境变量

- `FUNASR_MODEL`
- `FUNASR_VAD_MODEL`
- `FUNASR_PUNC_MODEL`

## 说明

- 镜像内使用 CPU 版 PyTorch 和 torchaudio，适合普通电脑或轻量 VPS。
- 第一次识别会下载模型，耗时会长一些。
- Docker Compose 会保留模型缓存卷，避免每次重启都重新下载。
- 更换网络环境时，只需要重新启动服务，并更新 ESP32 指向的新 IP 或内网穿透地址。
- Windows 上如果 Docker Desktop 配合 `127.0.0.1:7890` 这类本机代理使用，WSL NAT 模式可能无法访问 localhost 代理。可以在 `%USERPROFILE%\.wslconfig` 中加入下面配置，然后执行 `wsl --shutdown` 并重启 Docker Desktop：

```ini
[wsl2]
networkingMode=mirrored
autoProxy=true
dnsTunneling=true
firewall=true
```

## Windows 局域网排查记录

ESP32 项目里遇到过一次典型问题：

- Windows 主机本机访问 `http://127.0.0.1:10095/health` 正常。
- 通过电脑局域网 IP 访问 `http://<电脑局域网IP>:10095/health` 超时。
- ESP32 日志显示 `Local STT failed: err=ESP_ERR_HTTP_CONNECT`。

这说明 FunASR 容器本身是健康的，但局域网到 Docker 暴露端口的路径被防火墙、Docker 网络、路由隔离或跨网段访问挡住了。排查顺序：

1. 确认 Docker 端口发布正常：

```powershell
docker ps
docker port funasr-stt
```

期望看到：

```text
10095/tcp -> 0.0.0.0:10095
```

2. 在 Windows 主机上分别测试本机地址和局域网地址：

```powershell
Invoke-RestMethod http://127.0.0.1:10095/health
Invoke-RestMethod http://<电脑局域网IP>:10095/health
```

3. 如果本机地址正常、局域网地址超时，优先检查 Windows 防火墙是否允许入站 TCP `10095`，以及当前网络配置是否是“专用网络”。

4. 如果 ESP32 和电脑不在同一网段，例如 ESP32 是 `192.168.2.x`、电脑是 `192.168.1.x`，需要确认路由器允许 Wi-Fi 和有线 LAN 互访。访客 Wi-Fi 或 AP 隔离经常会拦截这种访问。

当时测试用的临时方案：

```powershell
python funasr_proxy_10096.py
```

这个代理监听 `0.0.0.0:10096`，并把 TCP 流量直通到 `127.0.0.1:10095`。它刻意保持简单的 TCP 直通，不再用第二层 HTTP 代理重新缓冲和转发，避免 ESP32 上传较大音频时代理卡住。然后把 ESP32 固件配置改成：

```c
#define APP_AI_STT_BASE_URL "http://<电脑局域网IP>:10096"
```

对于 `/asr_base64` 请求，代理还会记录 FunASR 返回的识别文本，以及上传 WAV 的时长、采样率、峰值 `peak` 和均方根 `rms`。排查唤醒失败时很有用：如果 `text` 为空，同时 `peak/rms` 很低，通常说明板子录到的声音太小，更像麦克风增益或采集音量问题，而不是 FunASR 服务不可达。

代理日志示例：

```text
192.168.1.4:62921 ASR text:  | wav 2.00s sr=16000 ch=1 peak=115 rms=17
```

这表示 ESP32 已经连到 FunASR，但上传音频几乎是静音。此时优先检查板载麦克风链路、固件软件增益、唤醒录音时长、说话距离。如果代理完全没有 ESP32 请求日志，则先排查网络。

`10096` 代理只是临时运行时辅助进程。电脑重启后需要重新启动；长期使用更建议修好 Docker 局域网端口、防火墙、路由隔离，或者部署稳定的反向代理/内网穿透。
