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
