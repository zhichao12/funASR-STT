# FunASR STT Service

Local FunASR speech-to-text service for the ESP32 board project.

## Docker First

Start with:

```bash
docker compose up -d --build
```

Or on Windows:

```powershell
.\run.ps1
```

Default endpoint:

```text
http://127.0.0.1:10095
```

For ESP32, use the LAN address of the host running Docker:

```text
http://192.168.1.23:10095
```

## API

- `GET /health`
- `POST /asr`
- `POST /asr_base64`

## Environment

Optional variables:

- `FUNASR_MODEL`
- `FUNASR_VAD_MODEL`
- `FUNASR_PUNC_MODEL`

## Notes

- The image uses CPU-only PyTorch and torchaudio.
- The first boot can take a while because the model is downloaded.
- Keep the container volume so model cache survives restarts.
- When the network changes, update the ESP32 `APP_AI_STT_BASE_URL` to the new host LAN IP, or put the service behind a tunnel/reverse proxy.
- On Windows, if Docker Desktop is used with a localhost proxy such as `127.0.0.1:7890`, WSL NAT mode can block the proxy. Add this to `%USERPROFILE%\.wslconfig`, then run `wsl --shutdown` and restart Docker Desktop:

```ini
[wsl2]
networkingMode=mirrored
autoProxy=true
dnsTunneling=true
firewall=true
```
