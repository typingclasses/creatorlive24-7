import { Check, Tag } from "lucide-react";

export const planPrice = (p) => (p.offer_active && p.offer_price != null ? p.offer_price : p.price);
export const rupees = (n) => `₹${Number(n).toLocaleString("en-IN")}`;
const period = (d) => (d === 30 ? "month" : d === 365 ? "year" : `${d} days`);

export const PlanCard = ({ plan, current, action }) => {
  const offer = plan.offer_active && plan.offer_price != null;
  return (
    <div data-testid={`plan-card-${plan.id}`} className={`relative bg-white border rounded-3xl p-7 flex flex-col transition-[transform,box-shadow] duration-300 hover:-translate-y-1 hover:shadow-xl ${current ? "border-[#10B981] ring-2 ring-[#10B981]/30" : offer ? "border-[#E50914]" : "border-slate-200"}`}>
      {offer && (
        <span className="absolute -top-3 left-6 flex items-center gap-1 bg-[#E50914] text-white text-[11px] font-bold px-3 py-1 rounded-full" data-testid={`plan-offer-badge-${plan.id}`}>
          <Tag className="w-3 h-3" /> {plan.offer_label || "Offer"}
        </span>
      )}
      {current && <span className="absolute -top-3 right-6 bg-[#10B981] text-white text-[11px] font-bold px-3 py-1 rounded-full">Your plan</span>}
      <h3 className="text-xl font-bold">{plan.name}</h3>
      <div className="mt-4 flex items-end gap-2">
        <span className="font-display text-4xl font-extrabold">{rupees(planPrice(plan))}</span>
        {offer && <span className="text-slate-400 line-through mb-1">{rupees(plan.price)}</span>}
        <span className="text-slate-500 text-sm mb-1">/ {period(plan.duration_days)}</span>
      </div>
      <ul className="mt-6 space-y-2 text-sm text-slate-600 flex-1">
        {plan.features.map((f) => <li key={f} className="flex gap-2"><Check className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />{f}</li>)}
      </ul>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};
