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

- The first boot can take a while because the model is downloaded.
- Keep the container volume so model cache survives restarts.
- When the network changes, update the ESP32 `APP_AI_STT_BASE_URL` to the new host LAN IP, or put the service behind a tunnel/reverse proxy.
