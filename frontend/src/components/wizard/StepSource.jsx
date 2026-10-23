import { useRef, useState } from "react";
import { ArrowLeft, Camera, Monitor, Video, Upload, ChevronRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useStudio } from "@/context/StudioContext";
import { useApi, errMsg } from "@/lib/api";
import { SourceToolbar } from "@/components/wizard/SourceToolbar";
import { LibraryPicker } from "@/components/wizard/LibraryPicker";

const Row = ({ active, icon: I, color, title, sub, onClick, id, children }) => (
  <div className={`border rounded-2xl transition-colors ${active ? "border-[#E50914] ring-1 ring-[#E50914]" : "border-slate-200 hover:border-slate-300"}`}>
    <button onClick={onClick} data-testid={id} className="w-full flex items-center gap-4 p-5 text-left">
      <span className="grid place-items-center w-12 h-12 rounded-full bg-slate-100"><I className={`w-5 h-5 ${color}`} /></span>
      <span className="flex-1 min-w-0"><span className="block text-lg font-medium">{title}</span><span className="block text-xs text-slate-500 truncate">{sub}</span></span>
      <ChevronRight className="w-4 h-4 text-slate-400" />
    </button>
    {children}
  </div>
);

export default function StepSource({ onBack, onNext }) {
  const { source, setSource, settings } = useStudio();
  const api = useApi();
  const fileRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [picker, setPicker] = useState(false);
  const h = settings.quality === "1080p" ? 1080 : 720;

  const pickCamera = async () => {
    try {
      const [w, hh] = settings.landscape ? [h * 16 / 9, h] : [h, h * 16 / 9];
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: w }, height: { ideal: hh }, frameRate: { ideal: settings.fps } }, audio: true });
      setSource({ type: "camera", stream });
      toast.success("Camera ready");
    } catch (e) { toast.error("Camera/mic permission was blocked: " + e.message); }
  };
  const pickScreen = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: settings.fps }, audio: true });
      setSource({ type: "screen", stream });
      toast.success("Screen capture ready");
    } catch (e) { toast.error("Screen sharing was cancelled"); }
  };
  const upload = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData(); fd.append("file", file);
      const v = await api.post("/videos", fd);
      setSource({ type: "video", video: v });
      toast.success("Video uploaded to your library");
    } catch (e) { toast.error(errMsg(e)); }
    finally { setUploading(false); fileRef.current.value = ""; }
  };
  const next = () => (source ? onNext() : toast.error("Choose a stream source first"));

  return (
    <div>
      <button onClick={onBack} data-testid="source-back-button" className="p-2 -ml-2 rounded-full hover:bg-slate-100"><ArrowLeft className="w-5 h-5" /></button>
      <h2 className="mt-3 text-3xl font-bold">Stream Source</h2>
      <p className="text-xs text-slate-500 mt-1">Destination: <b>Primary RTMP Stream</b> (Stream Key Ready)</p>
      <div className="mt-6 grid gap-3">
        <Row id="select-source-camera-button" active={source?.type === "camera"} icon={Camera} color="text-slate-700" title="Stream Camera" sub={`Front Webcam / Selfie Cam · ${settings.quality} @ ${settings.fps}fps`} onClick={pickCamera} />
        <Row id="select-source-screen-button" active={source?.type === "screen"} icon={Monitor} color="text-[#1D4ED8]" title="Screen Broadcast" sub="Capture Entire Screen, Window, or Browser Tab with Audio" onClick={pickScreen} />
        <Row id="select-source-video-button" active={source?.type === "video"} icon={Video} color="text-[#7C3AED]" title="Video" sub={source?.type === "video" ? `Cloud Video: ${source.video.title}` : "Stream a video from your cloud library"} onClick={() => setPicker(true)}>
          <div className="flex flex-wrap justify-between gap-2 px-5 pb-4 pt-3 border-t border-slate-100 mx-5">
            <input ref={fileRef} type="file" accept="video/*" hidden onChange={(e) => upload(e.target.files[0])} data-testid="video-file-input" />
            <button onClick={() => fileRef.current.click()} disabled={uploading} data-testid="choose-video-device-button" className="flex items-center gap-1.5 bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-xs font-semibold px-4 py-2 rounded-full transition-colors disabled:opacity-60">
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />} {uploading ? "Uploading…" : "Choose Video from Device"}
            </button>
            <button onClick={() => setPicker(true)} data-testid="open-video-studio-button" className="bg-[#E50914] hover:bg-[#C80711] text-white text-xs font-semibold px-4 py-2 rounded-full transition-colors">Open Video Studio ›</button>
          </div>
        </Row>
      </div>
      <SourceToolbar />
      <button onClick={next} data-testid="wizard-next-button" className="mt-6 w-full bg-[#E50914] hover:bg-[#C80711] text-white font-semibold py-4 rounded-2xl transition-colors">Next</button>
      <LibraryPicker open={picker} onOpenChange={setPicker} onPick={(v) => { setSource({ type: "video", video: v }); setPicker(false); }} />
    </div>
  );
}
