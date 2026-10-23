import asyncio
import ssl
from urllib.parse import urlsplit

# The bundled static ffmpeg can't resolve hostnames, so it connects to a local relay that does DNS + TLS (with SNI).


async def _pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError, ssl.SSLError):
        pass
    finally:
        writer.close()


async def open_relay(url: str):
    """Return (local rtmp url, server) forwarding to the real rtmp/rtmps url."""
    parts = urlsplit(url)
    tls = parts.scheme == "rtmps"
    host, port = parts.hostname, parts.port or (443 if tls else 1935)

    async def handle(local_r, local_w):
        try:
            up_r, up_w = await asyncio.open_connection(
                host, port, ssl=ssl.create_default_context() if tls else None, server_hostname=host if tls else None)
        except Exception:
            local_w.close()
            return
        await asyncio.gather(_pipe(local_r, up_w), _pipe(up_r, local_w))

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    local_port = server.sockets[0].getsockname()[1]
    return f"rtmp://127.0.0.1:{local_port}{parts.path}", server
