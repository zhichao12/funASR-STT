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

## ESP32 Quick Checklist

1. Start the service:

```powershell
.\run.ps1
```

2. Confirm the service is healthy on the host:

```powershell
Invoke-RestMethod http://127.0.0.1:10095/health
```

3. Find the host LAN IP, for example `192.168.1.2`, and test from a phone or
   another device on the same network as the ESP32:

```text
http://192.168.1.2:10095/health
```

4. If the LAN test works, configure the firmware with:

```c
#define APP_AI_STT_BASE_URL "http://192.168.1.2:10095"
```

5. If localhost works but LAN `10095` does not, start the Windows helper proxy:

```powershell
python funasr_proxy_10096.py
```

Then test:

```text
http://192.168.1.2:10096/health
```

and configure the firmware with:

```c
#define APP_AI_STT_BASE_URL "http://192.168.1.2:10096"
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

The proxy listens on `0.0.0.0:10096` and forwards TCP traffic to
`127.0.0.1:10095`. It is intentionally a simple TCP pass-through so larger
ESP32 audio uploads are not buffered or re-emitted by a second HTTP stack.
Then set the ESP32 firmware to:

```c
#define APP_AI_STT_BASE_URL "http://<host-lan-ip>:10096"
```

For `/asr_base64` calls, the proxy also logs the returned ASR text and basic
WAV statistics, for example duration, sample rate, peak, and RMS. This is useful
when wake-word detection fails: if `text` is empty and the RMS/peak are very
low, the issue is likely microphone gain or captured audio level rather than
FunASR reachability.

Example proxy log:

```text
192.168.1.4:62921 ASR text:  | wav 2.00s sr=16000 ch=1 peak=115 rms=17
```

This means the ESP32 reached FunASR, but the uploaded audio was almost silent.
In that case, check the board microphone path, firmware gain, wake recording
length, and speaking distance. If the proxy does not log ESP32 requests at all,
debug networking first.

This is only a runtime helper. For a stable setup, prefer fixing Docker LAN
publishing/firewall/routing or deploying the service behind a persistent reverse
proxy/tunnel.
