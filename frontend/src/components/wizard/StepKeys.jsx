import { useEffect, useState } from "react";
import { Eye, EyeOff, Youtube, Facebook, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { useApi, errMsg } from "@/lib/api";

const META = {
  youtube: { icon: Youtube, color: "text-[#E50914]", name: "YouTube", help: "https://studio.youtube.com/channel/UC/livestreaming", hint: "YouTube Studio → Go Live → Stream → Stream key" },
  facebook: { icon: Facebook, color: "text-[#1877F2]", name: "Facebook", help: "https://www.facebook.com/live/producer", hint: "Facebook Live Producer → Streaming software → Stream key" },
};

const PlatformCard = ({ p, value, onChange }) => {
  const [show, setShow] = useState(false);
  const m = META[p];
  const set = (k, v) => onChange({ ...value, [k]: v });
  return (
    <div className={`border rounded-2xl p-6 transition-colors ${value.enabled ? "border-[#E50914]/60 bg-red-50/30" : "border-slate-200"}`} data-testid={`${p}-destination-card`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3"><m.icon className={`w-7 h-7 ${m.color}`} /><span className="font-display text-lg font-bold">{m.name}</span></div>
        <Switch checked={value.enabled} onCheckedChange={(v) => set("enabled", v)} data-testid={`${p}-enabled-switch`} />
      </div>
      <div className="mt-5 grid gap-3">
        <label className="text-xs font-semibold text-slate-500">Server URL</label>
        <Input value={value.url} onChange={(e) => set("url", e.target.value)} className="font-mono text-xs" data-testid={`${p}-server-url-input`} />
        <label className="text-xs font-semibold text-slate-500">Stream key</label>
        <div className="relative">
          <Input type={show ? "text" : "password"} value={value.key} onChange={(e) => set("key", e.target.value)} placeholder="xxxx-xxxx-xxxx-xxxx" className="font-mono pr-10" data-testid={`${p}-stream-key-input`} />
          <button type="button" onClick={() => setShow(!show)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#0B132B]" data-testid={`${p}-toggle-key-visibility`}>
            {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <a href={m.help} target="_blank" rel="noreferrer" className="text-xs text-slate-500 hover:text-[#E50914] inline-flex items-center gap-1">{m.hint} <ExternalLink className="w-3 h-3" /></a>
      </div>
    </div>
  );
};

export default function StepKeys({ onNext }) {
  const api = useApi();
  const [dest, setDest] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.get("/destinations").then(setDest).catch((e) => toast.error(errMsg(e))); }, [api]);

  const save = async () => {
    if (!dest.youtube.enabled && !dest.facebook.enabled) return toast.error("Turn on at least one platform");
    setSaving(true);
    try { await api.put("/destinations", dest); toast.success("Stream keys saved"); onNext(); }
    catch (e) { toast.error(errMsg(e)); }
    finally { setSaving(false); }
  };

  if (!dest) return <Loader2 className="w-6 h-6 animate-spin mx-auto" />;
  return (
    <div>
      <h2 className="text-3xl font-bold">Stream Keys</h2>
      <p className="mt-1 text-sm text-slate-500">Turn on where you want to go live and paste the stream key. Keys are stored privately on your account.</p>
      <div className="mt-8 grid md:grid-cols-2 gap-5">
        {["youtube", "facebook"].map((p) => <PlatformCard key={p} p={p} value={dest[p]} onChange={(v) => setDest({ ...dest, [p]: v })} />)}
      </div>
      <button onClick={save} disabled={saving} data-testid="save-keys-next-button" className="mt-8 w-full bg-[#E50914] hover:bg-[#C80711] disabled:opacity-60 text-white font-semibold py-4 rounded-2xl transition-colors flex items-center justify-center gap-2">
        {saving && <Loader2 className="w-4 h-4 animate-spin" />} Save & Next
      </button>
    </div>
  );
}
