import { useCallback, useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { PlanCard, planPrice, rupees } from "@/components/PlanCard";
import { useApi, errMsg } from "@/lib/api";
import { useAppData } from "@/context/AppDataContext";

const STATUS = { pending: "bg-amber-100 text-amber-700", approved: "bg-emerald-100 text-emerald-700", rejected: "bg-red-100 text-red-700" };

const PayDialog = ({ plan, onClose, onDone }) => {
  const api = useApi();
  const { settings } = useAppData();
  const [utr, setUtr] = useState("");
  const [busy, setBusy] = useState(false);
  if (!plan) return null;
  const amount = planPrice(plan);
  const upi = `upi://pay?${new URLSearchParams({ pa: settings?.upi_id || "", pn: settings?.upi_name || "CreatorLive24/7", am: String(amount), cu: "INR", tn: `${plan.name} plan` })}`;
  const submit = async () => {
    setBusy(true);
    try { await api.post("/payments", { plan_id: plan.id, utr }); toast.success("Payment submitted. Admin will verify and activate your plan."); onDone(); }
    catch (e) { toast.error(errMsg(e)); }
    finally { setBusy(false); }
  };
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-md" data-testid="pay-dialog">
        <DialogHeader>
          <DialogTitle>Pay {rupees(amount)} for {plan.name}</DialogTitle>
          <DialogDescription>Scan with any UPI app (GPay, PhonePe, Paytm), pay, then enter the UPI transaction ID (UTR).</DialogDescription>
        </DialogHeader>
        {settings?.upi_id ? (
          <div className="grid place-items-center gap-3">
            <div className="p-4 bg-white border rounded-2xl" data-testid="upi-qr"><QRCodeSVG value={upi} size={200} /></div>
            <p className="font-mono text-sm" data-testid="upi-id-text">UPI ID: {settings.upi_id}</p>
            <a href={upi} className="text-xs text-[#1D4ED8] underline md:hidden" data-testid="upi-open-app-link">Open UPI app</a>
          </div>
        ) : <p className="text-sm text-[#E50914]" data-testid="upi-not-set">Payments are not set up yet. Please contact support.</p>}
        <label className="text-xs font-semibold text-slate-500 mt-2">UPI transaction ID / UTR</label>
        <Input value={utr} onChange={(e) => setUtr(e.target.value)} placeholder="e.g. 412345678901" data-testid="utr-input" />
        <button onClick={submit} disabled={busy || utr.trim().length < 6 || !settings?.upi_id} data-testid="submit-payment-button"
          className="w-full bg-[#E50914] hover:bg-[#C80711] disabled:opacity-50 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 transition-colors">
          {busy && <Loader2 className="w-4 h-4 animate-spin" />} I have paid — Submit
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default function Plans() {
  const api = useApi();
  const { me } = useAppData();
  const [plans, setPlans] = useState([]);
  const [mine, setMine] = useState([]);
  const [buying, setBuying] = useState(null);
  const load = useCallback(() => {
    api.get("/plans").then(setPlans).catch(() => {});
    api.get("/payments/mine").then(setMine).catch(() => {});
  }, [api]);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Plans</h1>
      <p className="mt-2 text-slate-500" data-testid="current-plan-text">
        {me?.plan_valid ? `Current plan: ${me.plan_name} · valid till ${new Date(me.plan_expires_at).toLocaleDateString()}` : "You don't have an active plan yet."}
      </p>
      <div className="mt-10 grid md:grid-cols-3 gap-6">
        {plans.map((p) => (
          <PlanCard key={p.id} plan={p} current={me?.plan_valid && me.plan_id === p.id}
            action={<button onClick={() => setBuying(p)} data-testid={`buy-plan-${p.id}`} className="w-full bg-[#0B132B] hover:bg-[#E50914] text-white font-semibold py-3 rounded-xl transition-colors">{me?.plan_valid && me.plan_id === p.id ? "Renew" : "Buy with UPI"}</button>} />
        ))}
      </div>
      {mine.length > 0 && (
        <div className="mt-12 bg-white border border-slate-200 rounded-3xl p-6" data-testid="my-payments">
          <h3 className="font-bold text-lg">My payment requests</h3>
          <ul className="mt-3 divide-y divide-slate-100 text-sm">
            {mine.map((p) => (
              <li key={p.id} className="py-3 flex flex-wrap gap-2 justify-between">
                <span>{p.plan_name} · {rupees(p.amount)} · <span className="font-mono">{p.utr}</span></span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${STATUS[p.status]}`}>{p.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <PayDialog plan={buying} onClose={() => setBuying(null)} onDone={() => { setBuying(null); load(); }} />
    </div>
  );
}
