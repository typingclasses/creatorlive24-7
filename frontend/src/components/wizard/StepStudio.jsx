import { useEffect, useRef, useState } from "react";
import { ArrowLeft, Radio, Square, Loader2, Youtube, Facebook, Film } from "lucide-react";
import { toast } from "sonner";
import { useStudio } from "@/context/StudioContext";
import { useApi, errMsg } from "@/lib/api";
import { startBrowserBroadcast } from "@/lib/broadcast";
import { LiveTimer } from "@/components/wizard/LiveTimer";

const Preview = ({ source }) => {
  const ref = useRef(null);
  useEffect(() => { if (ref.current && source?.stream) ref.current.srcObject = source.stream; }, [source]);
  if (source?.stream) return <video ref={ref} autoPlay muted playsInline data-testid="studio-preview-video" className="w-full h-full object-contain bg-black" />;
  return (
    <div className="w-full h-full grid place-items-center text-slate-400 text-center p-6">
      {source?.video ? <div><Film className="w-12 h-12 mx-auto text-[#7C3AED]" /><p className="mt-3 text-white font-semibold">{source.video.title}</p><p className="text-xs">Streams from the cloud server</p></div> : <p>No source selected</p>}
    </div>
  );
};

export default function StepStudio({ onBack }) {
  const { source, settings, status, refreshStatus } = useStudio();
  const api = useApi();
  const [busy, setBusy] = useState(false);
  const [dest, setDest] = useState(null);
  const bc = useRef(null);

  useEffect(() => { api.get("/destinations").then(setDest).catch(() => {}); }, [api]);
  useEffect(() => () => bc.current?.stop(), []);

  const goLive = async () => {
    if (!source) return toast.error("Pick a stream source in Step 2");
    setBusy(true);
    try {
      if (source.type === "video") {
        await api.post("/streams/video", { video_id: source.video.id, loop: settings.loop, quality: settings.quality, fps: settings.fps });
      } else {
        const token = await api.getToken();
        bc.current = startBrowserBroadcast({ stream: source.stream, token, kind: source.type, quality: settings.quality, fps: settings.fps, onError: (m) => toast.error(m) });
        await bc.current.ready;
        source.stream.getVideoTracks()[0].onended = () => endStream();
      }
      toast.success("You're live!");
      setTimeout(refreshStatus, 1500);
    } catch (e) { bc.current?.stop(); toast.error(errMsg(e)); }
    finally { setBusy(false); }
  };

  const endStream = async () => {
    setBusy(true);
    bc.current?.stop(); bc.current = null;
    try { await api.post("/streams/stop"); toast.success("Stream ended"); } catch (e) { toast.error(errMsg(e)); }
    await refreshStatus(); setBusy(false);
  };

  return (
    <div>
      <button onClick={onBack} data-testid="studio-back-button" className="p-2 -ml-2 rounded-full hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
      <div className="mt-3 flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-3xl font-bold">Go Live Studio</h2>
        <div className="flex gap-2 text-xs font-semibold">
          {dest?.youtube?.enabled && <span className="flex items-center gap-1 bg-slate-100 px-3 py-1.5 rounded-full"><Youtube className="w-4 h-4 text-[#E50914]" /> YouTube</span>}
          {dest?.facebook?.enabled && <span className="flex items-center gap-1 bg-slate-100 px-3 py-1.5 rounded-full"><Facebook className="w-4 h-4 text-[#1877F2]" /> Facebook</span>}
        </div>
      </div>
      <div className="mt-6 relative aspect-video rounded-2xl overflow-hidden bg-[#0B0F19]">
        <Preview source={source} />
        {status.live && <span className="absolute top-4 left-4 flex items-center gap-1.5 bg-[#E50914] text-white text-xs font-bold px-3 py-1.5 rounded" data-testid="studio-live-badge"><span className="w-2 h-2 bg-white rounded-full live-dot" /> LIVE</span>}
        {status.live && <span className="absolute top-4 right-4 bg-black/60 text-white px-3 py-1.5 rounded"><LiveTimer startedAt={status.started_at} /></span>}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        {[["Source", status.live ? status.title : source?.video?.title || source?.type || "—"], ["Quality", `${settings.quality} · ${settings.fps}fps`], ["Status", status.live ? "Online" : "Offline"]].map(([k, v]) => (
          <div key={k} className="bg-slate-50 rounded-xl py-3"><p className="text-[10px] uppercase tracking-widest text-slate-400">{k}</p><p className="font-mono text-sm truncate px-2" data-testid={`studio-stat-${k.toLowerCase()}`}>{v}</p></div>
        ))}
      </div>
      {!status.live && status.last_error && <p className="mt-3 text-xs text-[#E50914] bg-red-50 rounded-lg p-3" data-testid="studio-last-error">Last stream stopped: {status.last_error}</p>}
      {status.log?.length > 0 && status.live && <p className="mt-3 text-[11px] font-mono text-amber-600 truncate" data-testid="studio-encoder-log">{status.log[status.log.length - 1]}</p>}
      {status.live ? (
        <button onClick={endStream} disabled={busy} data-testid="end-stream-button" className="mt-6 w-full bg-[#0B132B] hover:bg-black text-white font-semibold py-4 rounded-2xl flex items-center justify-center gap-2 transition-colors">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />} End Stream
        </button>
      ) : (
        <button onClick={goLive} disabled={busy} data-testid="go-live-start-button" className="mt-6 w-full bg-[#E50914] hover:bg-[#C80711] disabled:opacity-60 text-white font-semibold py-4 rounded-2xl flex items-center justify-center gap-2 transition-colors">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Radio className="w-4 h-4" />} Go Live
        </button>
      )}
      <p className="mt-3 text-xs text-slate-500 text-center">{source?.type === "video" ? "Library videos keep streaming from our server even if you close this tab." : "Keep this tab open while streaming your camera or screen."}</p>
    </div>
  );
}
