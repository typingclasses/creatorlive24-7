import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, Film, Trash2, Play, Radio, Loader2, Smartphone, MonitorPlay } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { useApi, errMsg, formatSize, API } from "@/lib/api";
import { uploadVideo, formatLength } from "@/lib/upload";
import { useStudio } from "@/context/StudioContext";

const PreviewDialog = ({ video, onClose }) => {
  const api = useApi();
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!video) return setUrl(null);
    api.getToken().then((t) => setUrl(`${API}/videos/${video.id}/file?auth=${encodeURIComponent(t)}`));
  }, [video, api]);
  return (
    <Dialog open={!!video} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl" data-testid="video-preview-dialog">
        <DialogHeader><DialogTitle className="truncate pr-6">{video?.title}</DialogTitle></DialogHeader>
        <div className={`${video?.format === "short" ? "aspect-[9/16] max-h-[70vh] mx-auto" : "aspect-video"} bg-black rounded-xl grid place-items-center overflow-hidden`}>
          {url ? <video src={url} controls autoPlay className="w-full h-full" /> : <Loader2 className="w-6 h-6 animate-spin text-white" />}
        </div>
      </DialogContent>
    </Dialog>
  );
};

const TABS = [["all", "All"], ["long", "Long Format"], ["short", "Short Format"]];

const VideoCard = ({ v, onStream, onPreview, onDelete, onToggle }) => (
  <div className="bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-lg transition-shadow" data-testid={`video-card-${v.id}`}>
    <div className="relative aspect-video rounded-xl bg-gradient-to-br from-[#0B132B] to-[#1D4ED8] grid place-items-center">
      {v.format === "short" ? <Smartphone className="w-10 h-10 text-white/70" /> : <Film className="w-10 h-10 text-white/70" />}
      {v.duration != null && <span className="absolute bottom-2 right-2 bg-black/70 text-white text-[11px] font-mono px-1.5 py-0.5 rounded">{formatLength(v.duration)}</span>}
    </div>
    <div className="mt-4 flex items-center gap-2">
      <p className="flex-1 font-semibold truncate" title={v.title}>{v.title}</p>
      <button onClick={onToggle} title="Switch format" data-testid={`format-badge-${v.id}`}
        className={`text-[10px] font-bold uppercase px-2 py-1 rounded-full transition-colors ${v.format === "short" ? "bg-[#7C3AED]/10 text-[#7C3AED] hover:bg-[#7C3AED]/20" : "bg-[#1D4ED8]/10 text-[#1D4ED8] hover:bg-[#1D4ED8]/20"}`}>
        {v.format === "short" ? "Short" : "Long"}
      </button>
    </div>
    <p className="text-xs text-slate-500 font-mono">{formatSize(v.size)}{v.width ? ` · ${v.width}×${v.height}` : ""} · {new Date(v.created_at).toLocaleDateString()}</p>
    <div className="mt-4 flex gap-2">
      <button onClick={onStream} data-testid={`stream-video-${v.id}`} className="flex-1 flex items-center justify-center gap-1.5 bg-[#E50914] hover:bg-[#C80711] text-white text-xs font-semibold py-2 rounded-full transition-colors"><Radio className="w-3.5 h-3.5" /> Stream</button>
      <button onClick={onPreview} data-testid={`preview-video-${v.id}`} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200"><Play className="w-4 h-4" /></button>
      <button onClick={onDelete} data-testid={`delete-video-${v.id}`} className="p-2 rounded-full bg-slate-100 hover:bg-red-100 hover:text-[#E50914]"><Trash2 className="w-4 h-4" /></button>
    </div>
  </div>
);

export default function Library() {
  const api = useApi();
  const navigate = useNavigate();
  const { setSource } = useStudio();
  const [videos, setVideos] = useState([]);
  const [progress, setProgress] = useState(null);
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState(null);
  const [tab, setTab] = useState("all");
  const input = useRef(null);

  const load = useCallback(() => api.get("/videos").then(setVideos).catch((e) => toast.error(errMsg(e))), [api]);
  useEffect(() => { load(); }, [load]);

  const upload = async (file) => {
    if (!file) return;
    setProgress(0);
    try {
      const v = await uploadVideo(api, file, setProgress);
      toast.success(`Uploaded as ${v.format === "short" ? "Short" : "Long"} Format`);
      load();
    } catch (e) { toast.error(errMsg(e)); }
    finally { setProgress(null); input.current.value = ""; }
  };
  const remove = async (v) => { try { await api.del(`/videos/${v.id}`); toast.success("Removed"); load(); } catch (e) { toast.error(errMsg(e)); } };
  const toggle = async (v) => { try { await api.patch(`/videos/${v.id}`, { format: v.format === "short" ? "long" : "short" }); load(); } catch (e) { toast.error(errMsg(e)); } };
  const streamIt = (v) => { setSource({ type: "video", video: v }); navigate("/setup?step=3"); };
  const shown = videos.filter((v) => tab === "all" || (v.format || "long") === tab);
  const uploading = progress !== null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Video Library</h1>
      <p className="mt-2 text-slate-500">Upload Long Format and Short Format videos to the cloud, then stream them live any time.</p>
      <div onClick={() => !uploading && input.current.click()} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); !uploading && upload(e.dataTransfer.files[0]); }} data-testid="upload-video-dropzone"
        className={`mt-8 cursor-pointer border-2 border-dashed rounded-3xl p-12 text-center transition-colors ${drag ? "border-[#E50914] bg-red-50" : "border-slate-300 bg-white hover:border-[#1D4ED8]"}`}>
        <input ref={input} type="file" accept="video/*" hidden onChange={(e) => upload(e.target.files[0])} data-testid="library-file-input" />
        {uploading ? <Loader2 className="w-10 h-10 mx-auto animate-spin text-[#1D4ED8]" /> : <UploadCloud className="w-10 h-10 mx-auto text-[#1D4ED8]" />}
        <p className="mt-4 font-display text-lg font-semibold">{uploading ? `Uploading… ${progress}%` : "Drop a video here or click to upload"}</p>
        {uploading ? <Progress value={progress} className="mt-4 max-w-md mx-auto h-2" data-testid="upload-progress" /> : (
          <p className="text-xs text-slate-500 mt-1 flex items-center justify-center gap-3">
            <span className="flex items-center gap-1"><MonitorPlay className="w-3.5 h-3.5" /> Long Format</span>
            <span className="flex items-center gap-1"><Smartphone className="w-3.5 h-3.5" /> Short Format</span>
            · MP4, MOV, WEBM · up to 5 GB
          </p>
        )}
      </div>
      <div className="mt-10 flex gap-2" data-testid="library-tabs">
        {TABS.map(([k, label]) => (
          <button key={k} onClick={() => setTab(k)} data-testid={`library-tab-${k}`}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-colors ${tab === k ? "bg-[#0B132B] text-white" : "bg-white border border-slate-200 text-slate-600 hover:text-[#0B132B]"}`}>
            {label} <span className="opacity-60">({k === "all" ? videos.length : videos.filter((v) => (v.format || "long") === k).length})</span>
          </button>
        ))}
      </div>
      {shown.length === 0 ? <p className="mt-6 text-sm text-slate-500" data-testid="library-empty">No videos here yet.</p> : (
        <div className="mt-6 grid sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="library-grid">
          {shown.map((v) => (
            <VideoCard key={v.id} v={v} onStream={() => streamIt(v)} onPreview={() => setPreview(v)} onDelete={() => remove(v)} onToggle={() => toggle(v)} />
          ))}
        </div>
      )}
      <PreviewDialog video={preview} onClose={() => setPreview(null)} />
    </div>
  );
}
