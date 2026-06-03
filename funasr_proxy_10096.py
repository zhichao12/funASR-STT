import base64
import json
import socket
import socketserver
import struct
import threading

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 10095
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 10096
BUFFER_SIZE = 65536
CAPTURE_LIMIT = 2 * 1024 * 1024


def wav_stats(wav):
    if len(wav) < 44 or wav[0:4] != b"RIFF" or wav[8:12] != b"WAVE":
        return "not-wav"

    offset = 12
    sample_rate = 0
    channels = 0
    bits = 0
    data = b""
    while offset + 8 <= len(wav):
        chunk_id = wav[offset:offset + 4]
        chunk_size = struct.unpack_from("<I", wav, offset + 4)[0]
        chunk_start = offset + 8
        chunk_end = min(chunk_start + chunk_size, len(wav))
        if chunk_id == b"fmt " and chunk_size >= 16:
            _, channels, sample_rate, _, _, bits = struct.unpack_from("<HHIIHH", wav, chunk_start)
        elif chunk_id == b"data":
            data = wav[chunk_start:chunk_end]
            break
        offset = chunk_end + (chunk_size & 1)

    if bits != 16 or channels <= 0 or sample_rate <= 0 or len(data) < 2:
        return f"wav unsupported sr={sample_rate} ch={channels} bits={bits} data={len(data)}"

    sample_count = len(data) // 2
    if sample_count == 0:
        return f"wav empty sr={sample_rate} ch={channels}"

    peak = 0
    sum_squares = 0
    for (sample,) in struct.iter_unpack("<h", data[:sample_count * 2]):
        magnitude = abs(sample)
        if magnitude > peak:
            peak = magnitude
        sum_squares += sample * sample
    rms = int((sum_squares / sample_count) ** 0.5)
    duration = sample_count / sample_rate / channels
    return f"wav {duration:.2f}s sr={sample_rate} ch={channels} peak={peak} rms={rms}"


def maybe_log_asr_text(peer, request_head, response_head):
    try:
        first_line = request_head.split(b"\r\n", 1)[0].decode("ascii", errors="replace")
        if "/asr_base64" not in first_line:
            return

        _, request_body = request_head.split(b"\r\n\r\n", 1)
        audio_info = "audio=unknown"
        try:
            request_json = json.loads(request_body.decode("utf-8", errors="replace"))
            audio_b64 = request_json.get("audio_base64", "")
            if audio_b64:
                audio_info = wav_stats(base64.b64decode(audio_b64))
        except Exception as exc:
            audio_info = f"audio-log-skipped:{exc}"

        _, body = response_head.split(b"\r\n\r\n", 1)
        data = json.loads(body.decode("utf-8", errors="replace"))
        text = data.get("text", "")
        print(f"{peer} ASR text: {text} | {audio_info}", flush=True)
    except Exception as exc:
        print(f"{peer} ASR text log skipped: {exc}", flush=True)


def relay(src, dst, label, context=None, direction=""):
    captured = bytearray()
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            if context is not None and len(captured) < CAPTURE_LIMIT:
                captured.extend(data[:CAPTURE_LIMIT - len(captured)])
            dst.sendall(data)
    except OSError as exc:
        print(f"{label} closed: {exc}", flush=True)
    finally:
        if context is not None:
            if direction == "client":
                context["request"] = bytes(captured)
            elif direction == "upstream":
                context["response"] = bytes(captured)
        try:
            dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        peer = f"{self.client_address[0]}:{self.client_address[1]}"
        try:
            upstream = socket.create_connection((TARGET_HOST, TARGET_PORT), timeout=10)
        except OSError as exc:
            print(f"{peer} connect upstream failed: {exc}", flush=True)
            return

        print(f"{peer} -> {TARGET_HOST}:{TARGET_PORT}", flush=True)
        context = {}
        with upstream:
            threads = [
                threading.Thread(target=relay, args=(self.request, upstream, f"{peer} client", context, "client"), daemon=True),
                threading.Thread(target=relay, args=(upstream, self.request, f"{peer} upstream", context, "upstream"), daemon=True),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        maybe_log_asr_text(peer, context.get("request", b""), context.get("response", b""))
        print(f"{peer} disconnected", flush=True)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with Server((LISTEN_HOST, LISTEN_PORT), Handler) as server:
        print(f"tcp proxy listening on {LISTEN_HOST}:{LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT}", flush=True)
        server.serve_forever()
