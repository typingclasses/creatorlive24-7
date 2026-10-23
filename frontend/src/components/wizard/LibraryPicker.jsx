import { useEffect, useState } from "react";
import { Film, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useApi, formatSize } from "@/lib/api";

export const LibraryPicker = ({ open, onOpenChange, onPick }) => {
  const api = useApi();
  const [videos, setVideos] = useState(null);
  useEffect(() => { if (open) api.get("/videos").then(setVideos).catch(() => setVideos([])); }, [open, api]);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="library-picker-dialog" className="max-w-lg">
        <DialogHeader><DialogTitle>Video Studio · pick a video</DialogTitle></DialogHeader>
        {!videos ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : videos.length === 0 ? (
          <p className="text-sm text-slate-500">Your library is empty. Use "Choose Video from Device" to upload one.</p>
        ) : (
          <ul className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {videos.map((v) => (
              <li key={v.id}>
                <button onClick={() => onPick(v)} data-testid={`pick-video-${v.id}`} className="w-full flex items-center gap-3 py-3 px-2 rounded-lg text-left hover:bg-slate-50">
                  <Film className="w-5 h-5 text-[#7C3AED]" />
                  <span className="flex-1 truncate text-sm font-medium">{v.title}</span>
                  <span className="text-xs text-slate-400 font-mono">{formatSize(v.size)}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
};
