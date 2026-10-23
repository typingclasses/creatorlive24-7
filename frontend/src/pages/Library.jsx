import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, Film, Trash2, Play, Radio, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useApi, errMsg, formatSize } from "@/lib/api";
import { useStudio } from "@/context/StudioContext";

const PreviewDialog = ({ video, onClose }) => {
  const api = useApi();
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!video) return;
    let u;
    api.get(`/videos/${video.id}/file`, { responseType: "blob" }).then((b) => { u = URL.createObjectURL(b); setUrl(u); }).catch((e) => toast.error(errMsg(e)));
    return () => { u && URL.revokeObjectURL(u); setUrl(null); };
  }, [video, api]);
  return (
    <Dialog open={!!video} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-3xl" data-testid="video-preview-dialog">
        <DialogHeader><DialogTitle className="truncate pr-6">{video?.title}</DialogTitle></DialogHeader>
        <div className="aspect-video bg-black rounded-xl grid place-items-center overflow-hidden">
          {url ? <video src={url} controls autoPlay className="w-full h-full" /> : <Loader2 className="w-6 h-6 animate-spin text-white" />}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default function Library() {
  const api = useApi();
  const navigate = useNavigate();
  const { setSource } = useStudio();
  const [videos, setVideos] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState(null);
  const input = useRef(null);

  const load = useCallback(() => api.get("/videos").then(setVideos).catch((e) => toast.error(errMsg(e))), [api]);
  useEffect(() => { load(); }, [load]);

  const upload = async (file) => {
    if (!file) return;
    setUploading(true);
    try { const fd = new FormData(); fd.append("file", file); await api.post("/videos", fd); toast.success("Uploaded"); load(); }
    catch (e) { toast.error(errMsg(e)); }
    finally { setUploading(false); input.current.value = ""; }
  };
  const remove = async (v) => { try { await api.del(`/videos/${v.id}`); toast.success("Removed"); load(); } catch (e) { toast.error(errMsg(e)); } };
  const streamIt = (v) => { setSource({ type: "video", video: v }); navigate("/setup?step=3"); };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Video Library</h1>
      <p className="mt-2 text-slate-500">Upload videos to the cloud, then stream them live any time.</p>
      <div onClick={() => !uploading && input.current.click()} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files[0]); }} data-testid="upload-video-dropzone"
        className={`mt-8 cursor-pointer border-2 border-dashed rounded-3xl p-12 text-center transition-colors ${drag ? "border-[#E50914] bg-red-50" : "border-slate-300 bg-white hover:border-[#1D4ED8]"}`}>
        <input ref={input} type="file" accept="video/*" hidden onChange={(e) => upload(e.target.files[0])} data-testid="library-file-input" />
        {uploading ? <Loader2 className="w-10 h-10 mx-auto animate-spin text-[#1D4ED8]" /> : <UploadCloud className="w-10 h-10 mx-auto text-[#1D4ED8]" />}
        <p className="mt-4 font-display text-lg font-semibold">{uploading ? "Uploading…" : "Drop a video here or click to upload"}</p>
        <p className="text-xs text-slate-500 mt-1">MP4, MOV, WEBM · up to 1 GB</p>
      </div>
      {videos.length === 0 ? <p className="mt-10 text-sm text-slate-500" data-testid="library-empty">No videos yet.</p> : (
        <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-5" data-testid="library-grid">
          {videos.map((v) => (
            <div key={v.id} className="bg-white border border-slate-200 rounded-2xl p-5 hover:shadow-lg transition-shadow" data-testid={`video-card-${v.id}`}>
              <div className="aspect-video rounded-xl bg-gradient-to-br from-[#0B132B] to-[#1D4ED8] grid place-items-center"><Film className="w-10 h-10 text-white/70" /></div>
              <p className="mt-4 font-semibold truncate" title={v.title}>{v.title}</p>
              <p className="text-xs text-slate-500 font-mono">{formatSize(v.size)} · {new Date(v.created_at).toLocaleDateString()}</p>
              <div className="mt-4 flex gap-2">
                <button onClick={() => streamIt(v)} data-testid={`stream-video-${v.id}`} className="flex-1 flex items-center justify-center gap-1.5 bg-[#E50914] hover:bg-[#C80711] text-white text-xs font-semibold py-2 rounded-full transition-colors"><Radio className="w-3.5 h-3.5" /> Stream</button>
                <button onClick={() => setPreview(v)} data-testid={`preview-video-${v.id}`} className="p-2 rounded-full bg-slate-100 hover:bg-slate-200"><Play className="w-4 h-4" /></button>
                <button onClick={() => remove(v)} data-testid={`delete-video-${v.id}`} className="p-2 rounded-full bg-slate-100 hover:bg-red-100 hover:text-[#E50914]"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}
      <PreviewDialog video={preview} onClose={() => setPreview(null)} />
    </div>
  );
}
