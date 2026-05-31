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

Always test the exact URL from a phone or another device on the same network as
the ESP32 before flashing firmware:

```text
http://<host-lan-ip>:10095/health
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

## Windows LAN Troubleshooting

Observed issue from the ESP32 project:

- `http://127.0.0.1:10095/health` worked on the Windows host.
- `http://<host-lan-ip>:10095/health` timed out from the host LAN address and
  from a phone on the board network.
- ESP32 logs showed `Local STT failed: err=ESP_ERR_HTTP_CONNECT`.

This means the model service is healthy, but the LAN path to Docker is blocked
or not routed. Check these in order:

1. Confirm Docker is publishing the port:

```powershell
docker ps
docker port funasr-stt
```

Expected:

```text
10095/tcp -> 0.0.0.0:10095
```

2. Test localhost and LAN separately on the Windows host:

```powershell
Invoke-RestMethod http://127.0.0.1:10095/health
Invoke-RestMethod http://<host-lan-ip>:10095/health
```

3. If localhost works but LAN times out, allow inbound TCP `10095` in Windows
   Firewall, or change the network profile from Public to Private.

4. If the ESP32 is on a different subnet, for example ESP32 `192.168.2.x` and
   host `192.168.1.x`, make sure the router allows traffic between the Wi-Fi and
   wired LAN. Guest Wi-Fi/AP isolation commonly blocks this.

Temporary workaround used during testing:

```powershell
python funasr_proxy_10096.py
```

The proxy listens on `0.0.0.0:10096` and forwards requests to
`http://127.0.0.1:10095`. Then set the ESP32 firmware to:

```c
#define APP_AI_STT_BASE_URL "http://<host-lan-ip>:10096"
```

This is only a runtime helper. For a stable setup, prefer fixing Docker LAN
publishing/firewall/routing or deploying the service behind a persistent reverse
proxy/tunnel.
