# FunASR STT 服务

这是给 ESP32 板子用的本地语音转文字服务。

## 一键启动

```bash
docker compose up -d --build
```

启动后默认地址：

```text
http://127.0.0.1:10095
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

- 第一次启动会下载模型，时间会长一点。
- 换网络时，只要更新 ESP32 指向的新 IP，或者用内网穿透把服务暴露出来即可。
- 容器模式下建议保留模型缓存卷，避免每次重启都重新下载。

