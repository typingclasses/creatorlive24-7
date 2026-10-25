import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2, Upload, RotateCcw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { useApi, errMsg, BACKEND_URL } from "@/lib/api";
import { useAppData } from "@/context/AppDataContext";

const Field = ({ label, children }) => <label className="grid gap-1 text-xs font-semibold text-slate-500">{label}{children}</label>;
const Section = ({ title, children }) => (
  <div className="bg-white border border-slate-200 rounded-3xl p-6">
    <h3 className="text-lg font-bold mb-4">{title}</h3>
    <div className="grid sm:grid-cols-2 gap-4">{children}</div>
  </div>
);

export default function AdminSettings() {
  const api = useApi();
  const { settings, loadSettings } = useAppData();
  const [f, setF] = useState(null);
  const [busy, setBusy] = useState(false);
  const [logoBusy, setLogoBusy] = useState(false);
  const logoInput = useRef(null);
  useEffect(() => { if (settings && !f) setF(settings); }, [settings, f]);
  if (!f) return <Loader2 className="w-5 h-5 animate-spin mx-auto" />;
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }));
  const setSocial = (k, v) => setF((x) => ({ ...x, social: { ...x.social, [k]: v } }));
  const cls = "bg-white text-[#0B132B] placeholder:text-slate-400 placeholder:italic";
  const inp = (k, ph) => <Input value={f[k] || ""} placeholder={ph ? `e.g. ${ph}` : ""} className={cls} onChange={(e) => set(k, e.target.value)} data-testid={`settings-${k}-input`} />;
  const fixUrl = (u) => (u && !/^https?:\/\//i.test(u.trim()) ? `https://${u.trim()}` : (u || "").trim());

  const uploadLogo = async (file) => {
    if (!file) return;
    setLogoBusy(true);
    try {
      const fd = new FormData(); fd.append("file", file);
      await api.post("/admin/watermark", fd);
      toast.success("New logo uploaded — it will show on free users' next live stream");
      loadSettings();
    } catch (e) { toast.error(errMsg(e)); }
    finally { setLogoBusy(false); logoInput.current.value = ""; }
  };
  const resetLogo = async () => {
    setLogoBusy(true);
    try { await api.del("/admin/watermark"); toast.success("Default CreatorLive24/7 logo restored"); loadSettings(); }
    catch (e) { toast.error(errMsg(e)); }
    finally { setLogoBusy(false); }
  };
  const toggleLogo = async (v) => {
    set("watermark_enabled", v);
    try { await api.put("/admin/settings", { ...settings, watermark_enabled: v }); toast.success(v ? "Logo will show on free users' streams" : "Logo hidden for everyone"); loadSettings(); }
    catch (e) { set("watermark_enabled", !v); toast.error(errMsg(e)); }
  };
  const save = async () => {
    setBusy(true);
    const body = { ...f, social: Object.fromEntries(Object.entries(f.social || {}).map(([k, v]) => [k, fixUrl(v)])) };
    try { const saved = await api.put("/admin/settings", body); setF((x) => ({ ...x, ...saved })); toast.success("Main page settings updated"); loadSettings(); }
    catch (e) { toast.error(errMsg(e)); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-6">
      <Section title="Main page">
        <Field label="Website name">{inp("site_name")}</Field>
        <Field label="Tagline">{inp("tagline")}</Field>
        <Field label="Business address">{inp("address")}</Field>
      </Section>
      <div className="bg-white border border-slate-200 rounded-3xl p-6 flex flex-wrap items-center gap-6 justify-between" data-testid="settings-watermark-card">
        <div className="flex items-center gap-4">
          <div className="h-14 min-w-[120px] px-3 grid place-items-center rounded-xl border bg-[repeating-conic-gradient(#e2e8f0_0%_25%,#fff_0%_50%)] bg-[length:16px_16px]">
            <img src={`${BACKEND_URL}/api/watermark?v=${settings?.watermark_version || "0"}`} alt="Current logo" data-testid="settings-watermark-preview" className="max-h-10 max-w-[200px] object-contain" />
          </div>
          <div>
            <h3 className="text-lg font-bold">Logo on free users' live stream</h3>
            <p className="text-sm text-slate-500">Shown at top-left for users without a paid plan. Paid users never get it. Best: transparent PNG, wide logo.</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input ref={logoInput} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={(e) => uploadLogo(e.target.files[0])} data-testid="settings-watermark-file-input" />
          <button onClick={() => logoInput.current.click()} disabled={logoBusy} data-testid="settings-watermark-upload-button" className="flex items-center gap-1.5 bg-[#0B132B] hover:bg-[#1D4ED8] disabled:opacity-60 text-white text-xs font-semibold px-4 py-2 rounded-full transition-colors">
            {logoBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />} Upload new logo
          </button>
          {settings?.watermark_path && (
            <button onClick={resetLogo} disabled={logoBusy} data-testid="settings-watermark-reset-button" className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-xs font-semibold px-4 py-2 rounded-full transition-colors">
              <RotateCcw className="w-3.5 h-3.5" /> Use default
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">{f.watermark_enabled !== false ? "Showing" : "Hidden"}</span>
          <Switch checked={f.watermark_enabled !== false} onCheckedChange={toggleLogo} data-testid="settings-watermark-switch" />
        </div>
      </div>
      <Section title="Support Us">
        <Field label="Mobile number">{inp("mobile", "+91 98765 43210")}</Field>
        <Field label="WhatsApp number">{inp("whatsapp", "+91 98765 43210")}</Field>
        <Field label="Support email">{inp("support_email", "support@example.com")}</Field>
        <Field label="Support message"><Textarea rows={2} className={cls} value={f.support_text || ""} onChange={(e) => set("support_text", e.target.value)} data-testid="settings-support_text-input" /></Field>
      </Section>
      <Section title="Social media links">
        {["youtube", "facebook", "instagram", "twitter"].map((k) => (
          <Field key={k} label={k === "twitter" ? "X (Twitter)" : k[0].toUpperCase() + k.slice(1)}>
            <Input value={f.social?.[k] || ""} placeholder={`e.g. https://${k === "twitter" ? "x" : k}.com/yourpage`} className={cls} onChange={(e) => setSocial(k, e.target.value)} data-testid={`settings-social-${k}-input`} />
          </Field>
        ))}
      </Section>
      <Section title="UPI payments (QR code)">
        <Field label="UPI ID">{inp("upi_id", "yourname@okaxis")}</Field>
        <Field label="Payee name shown in UPI app">{inp("upi_name")}</Field>
      </Section>
      <button onClick={save} disabled={busy} data-testid="settings-save-button" className="w-full sm:w-auto px-10 bg-[#E50914] hover:bg-[#C80711] disabled:opacity-60 text-white font-semibold py-3.5 rounded-2xl flex items-center justify-center gap-2 transition-colors">
        {busy && <Loader2 className="w-4 h-4 animate-spin" />} Save settings
      </button>
    </div>
  );
}
