import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApi, errMsg } from "@/lib/api";
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
  useEffect(() => { if (settings && !f) setF(settings); }, [settings, f]);
  if (!f) return <Loader2 className="w-5 h-5 animate-spin mx-auto" />;
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }));
  const setSocial = (k, v) => setF((x) => ({ ...x, social: { ...x.social, [k]: v } }));
  const cls = "bg-white text-[#0B132B] placeholder:text-slate-300 placeholder:italic";
  const inp = (k, ph) => <Input value={f[k] || ""} placeholder={ph ? `e.g. ${ph}` : ""} className={cls} onChange={(e) => set(k, e.target.value)} data-testid={`settings-${k}-input`} />;
  const fixUrl = (u) => (u && !/^https?:\/\//i.test(u.trim()) ? `https://${u.trim()}` : (u || "").trim());

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
