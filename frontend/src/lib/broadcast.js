import { BACKEND_URL } from "@/lib/api";

const pickMime = () => {
  const types = ["video/webm;codecs=vp8,opus", "video/webm;codecs=h264,opus", "video/webm", "video/mp4"];
  return types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
};

const withAudio = (stream) => {
  if (stream.getAudioTracks().length) return { stream, cleanup: () => {} };
  const ctx = new AudioContext();
  const dest = ctx.createMediaStreamDestination();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  gain.gain.value = 0;
  osc.connect(gain).connect(dest);
  osc.start();
  return { stream: new MediaStream([...stream.getVideoTracks(), dest.stream.getAudioTracks()[0]]), cleanup: () => ctx.close() };
};

// Sends the browser's MediaStream to the backend relay, which pushes it to RTMP.
export function startBrowserBroadcast({ stream, token, kind, quality, fps, onError }) {
  const qs = new URLSearchParams({ token, kind, quality, fps: String(fps) });
  const ws = new WebSocket(`${BACKEND_URL.replace(/^http/, "ws")}/api/ws/live?${qs}`);
  ws.binaryType = "arraybuffer";
  let recorder = null;
  const { stream: out, cleanup } = withAudio(stream);

  const ready = new Promise((resolve, reject) => {
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.error) { reject(new Error(msg.error)); onError?.(msg.error); return; }
      if (msg.ok && !recorder) {
        recorder = new MediaRecorder(out, { mimeType: pickMime(), videoBitsPerSecond: quality === "1080p" ? 5_000_000 : 3_000_000, audioBitsPerSecond: 128_000 });
        recorder.ondataavailable = async (e) => { if (e.data.size && ws.readyState === 1) ws.send(await e.data.arrayBuffer()); };
        recorder.start(1000);
        resolve();
      }
    };
    ws.onerror = () => reject(new Error("Could not connect to the streaming server"));
    ws.onclose = (e) => { if (!recorder) reject(new Error(e.code === 4401 ? "Session expired, sign in again" : "Connection closed")); };
  });

  const stop = () => {
    try { recorder && recorder.state !== "inactive" && recorder.stop(); } catch {}
    try { ws.close(); } catch {}
    cleanup();
  };
  return { ready, stop };
}
