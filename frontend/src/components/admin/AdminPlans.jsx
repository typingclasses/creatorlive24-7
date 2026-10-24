import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { PlanCard } from "@/components/PlanCard";
import { useApi, errMsg } from "@/lib/api";

const EMPTY = { name: "", price: 0, duration_days: 30, features: [], active: true, offer_active: false, offer_price: null, offer_label: "", sort: 0 };

const Field = ({ label, children }) => <label className="grid gap-1 text-xs font-semibold text-slate-500">{label}{children}</label>;

const PlanForm = ({ plan, onClose, onSaved }) => {
  const api = useApi();
  const [f, setF] = useState({ ...EMPTY, ...plan, featuresText: (plan?.features || []).join("\n") });
  const set = (k, v) => setF((x) => ({ ...x, [k]: v }));
  const save = async () => {
    const body = { name: f.name, price: Number(f.price), duration_days: Number(f.duration_days), features: f.featuresText.split("\n").map((x) => x.trim()).filter(Boolean),
      active: f.active, offer_active: f.offer_active, offer_price: f.offer_price === "" || f.offer_price == null ? null : Number(f.offer_price), offer_label: f.offer_label, sort: Number(f.sort) };
    if (body.offer_active && body.offer_price == null) return toast.error("Enter an offer price");
    try { plan?.id ? await api.put(`/admin/plans/${plan.id}`, body) : await api.post("/admin/plans", body); toast.success("Plan saved"); onSaved(); }
    catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto" data-testid="plan-form-dialog">
        <DialogHeader><DialogTitle>{plan?.id ? "Edit plan" : "New plan"}</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Plan name"><Input value={f.name} onChange={(e) => set("name", e.target.value)} data-testid="plan-name-input" /></Field>
          <Field label="Price (₹)"><Input type="number" value={f.price} onChange={(e) => set("price", e.target.value)} data-testid="plan-price-input" /></Field>
          <Field label="Duration (days)"><Input type="number" value={f.duration_days} onChange={(e) => set("duration_days", e.target.value)} data-testid="plan-duration-input" /></Field>
          <Field label="Order"><Input type="number" value={f.sort} onChange={(e) => set("sort", e.target.value)} data-testid="plan-sort-input" /></Field>
        </div>
        <Field label="Features (one per line)"><Textarea rows={4} value={f.featuresText} onChange={(e) => set("featuresText", e.target.value)} data-testid="plan-features-input" /></Field>
        <div className="flex items-center justify-between border rounded-xl p-3"><span className="text-sm font-medium">Plan visible to users</span><Switch checked={f.active} onCheckedChange={(v) => set("active", v)} data-testid="plan-active-switch" /></div>
        <div className="border rounded-xl p-3 space-y-3 bg-red-50/40">
          <div className="flex items-center justify-between"><span className="text-sm font-medium">Offer active</span><Switch checked={f.offer_active} onCheckedChange={(v) => set("offer_active", v)} data-testid="plan-offer-switch" /></div>
          {f.offer_active && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Offer price (₹)"><Input type="number" value={f.offer_price ?? ""} onChange={(e) => set("offer_price", e.target.value)} data-testid="plan-offer-price-input" /></Field>
              <Field label="Offer label"><Input value={f.offer_label} onChange={(e) => set("offer_label", e.target.value)} placeholder="Diwali Offer 40% OFF" data-testid="plan-offer-label-input" /></Field>
            </div>
          )}
        </div>
        <button onClick={save} data-testid="plan-save-button" className="w-full bg-[#E50914] hover:bg-[#C80711] text-white font-semibold py-3 rounded-xl transition-colors">Save plan</button>
      </DialogContent>
    </Dialog>
  );
};

export default function AdminPlans() {
  const api = useApi();
  const [plans, setPlans] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => api.get("/admin/plans").then(setPlans).catch((e) => toast.error(errMsg(e))), [api]);
  useEffect(() => { load(); }, [load]);
  const remove = async (p) => {
    if (!window.confirm(`Delete plan "${p.name}"?`)) return;
    try { await api.del(`/admin/plans/${p.id}`); toast.success("Plan deleted"); load(); } catch (e) { toast.error(errMsg(e)); }
  };
  const toggleOffer = async (p) => {
    if (!p.offer_active && p.offer_price == null) return setEditing({ ...p, offer_active: true });
    const { id, created_at, ...body } = p;
    try { await api.put(`/admin/plans/${id}`, { ...body, offer_active: !p.offer_active }); load(); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div>
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold">Plans & Offers</h3>
        <button onClick={() => setEditing({})} data-testid="add-plan-button" className="flex items-center gap-1.5 bg-[#0B132B] hover:bg-[#E50914] text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"><Plus className="w-4 h-4" /> Add plan</button>
      </div>
      <div className="mt-8 grid md:grid-cols-3 gap-6">
        {plans.map((p) => (
          <div key={p.id} className={`h-full [&>div]:h-full ${p.active ? "" : "opacity-60"}`}>
            <PlanCard plan={p} action={
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm"><span>Offer active</span><Switch checked={p.offer_active} onCheckedChange={() => toggleOffer(p)} data-testid={`plan-offer-toggle-${p.id}`} /></div>
                {!p.active && <p className="text-xs text-[#E50914] font-semibold">Hidden from users</p>}
                <div className="flex gap-2">
                  <button onClick={() => setEditing(p)} data-testid={`edit-plan-${p.id}`} className="flex-1 flex items-center justify-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-sm font-semibold py-2 rounded-xl"><Pencil className="w-4 h-4" /> Edit</button>
                  <button onClick={() => remove(p)} data-testid={`delete-plan-${p.id}`} className="p-2 rounded-xl bg-slate-100 hover:bg-red-100 hover:text-[#E50914]"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
            } />
          </div>
        ))}
      </div>
      {editing && <PlanForm plan={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}
