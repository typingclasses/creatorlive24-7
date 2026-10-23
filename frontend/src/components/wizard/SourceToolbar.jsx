import { useState } from "react";
import { Lightbulb, RectangleHorizontal, RectangleVertical, Repeat, Library } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useStudio } from "@/context/StudioContext";

const Tool = ({ label, onClick, id, active, children }) => (
  <button onClick={onClick} data-testid={id} className={`flex flex-col items-center gap-2 py-3 rounded-xl transition-colors hover:bg-slate-50 ${active ? "text-[#E50914]" : "text-slate-700"}`}>
    <span className="h-6 grid place-items-center">{children}</span>
    <span className="text-xs">{label}</span>
  </button>
);

const Chip = ({ children }) => <span className="border-2 border-current rounded px-1 text-[10px] font-bold font-mono">{children}</span>;

const tips = [
  "In YouTube Studio, enable your channel for live streaming (it can take up to 24 hours the first time).",
  "Use 720p if your internet upload speed is below 6 Mbps; 1080p needs around 8 Mbps.",
  "Camera and Screen streams run from this browser tab — keep it open while live.",
  "Library videos stream from our server, so they continue even if you close the tab.",
  "Turn on Replay to loop a library video continuously.",
];

export const SourceToolbar = () => {
  const { settings, setSettings } = useStudio();
  const [tipsOpen, setTipsOpen] = useState(false);
  const navigate = useNavigate();
  const set = (k, v) => setSettings((s) => ({ ...s, [k]: v }));
  return (
    <div className="mt-8 border border-slate-200 rounded-2xl p-3 grid grid-cols-3 sm:grid-cols-6 shadow-sm">
      <Tool label="Tips" id="toolbar-tips-button" onClick={() => setTipsOpen(true)}><Lightbulb className="w-5 h-5" /></Tool>
      <Tool label={settings.landscape ? "Landscape" : "Portrait"} id="toolbar-orientation-button" onClick={() => set("landscape", !settings.landscape)}>
        {settings.landscape ? <RectangleHorizontal className="w-5 h-5" /> : <RectangleVertical className="w-5 h-5" />}
      </Tool>
      <Tool label="Video quality" id="toolbar-quality-button" onClick={() => set("quality", settings.quality === "720p" ? "1080p" : "720p")}><Chip>{settings.quality === "1080p" ? "FHD" : "HD"}</Chip></Tool>
      <Tool label="FPS" id="toolbar-fps-button" onClick={() => set("fps", settings.fps === 30 ? 60 : 30)}><Chip>{settings.fps}</Chip></Tool>
      <Tool label={settings.loop ? "Replay on" : "Replay off"} id="toolbar-replay-button" active={settings.loop} onClick={() => set("loop", !settings.loop)}><Repeat className="w-5 h-5" /></Tool>
      <Tool label="Library" id="toolbar-library-button" onClick={() => navigate("/library")}><Library className="w-5 h-5" /></Tool>
      <Dialog open={tipsOpen} onOpenChange={setTipsOpen}>
        <DialogContent data-testid="tips-dialog">
          <DialogHeader><DialogTitle>Streaming tips</DialogTitle></DialogHeader>
          <ul className="space-y-3 text-sm text-slate-600 list-disc pl-5">{tips.map((t) => <li key={t}>{t}</li>)}</ul>
        </DialogContent>
      </Dialog>
    </div>
  );
};
