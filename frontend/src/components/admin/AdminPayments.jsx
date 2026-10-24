import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Check, X } from "lucide-react";
import { rupees } from "@/components/PlanCard";
import { useApi, errMsg } from "@/lib/api";

const FILTERS = [["pending", "To verify"], ["approved", "Approved"], ["rejected", "Rejected"], ["", "All"]];
const STATUS = { pending: "bg-amber-100 text-amber-700", approved: "bg-emerald-100 text-emerald-700", rejected: "bg-red-100 text-red-700" };

export default function AdminPayments() {
  const api = useApi();
  const [filter, setFilter] = useState("pending");
  const [rows, setRows] = useState([]);
  const load = useCallback(() => api.get(`/admin/payments${filter ? `?status=${filter}` : ""}`).then(setRows).catch((e) => toast.error(errMsg(e))), [api, filter]);
  useEffect(() => { load(); }, [load]);
  const decide = async (p, action) => {
    try { await api.post(`/admin/payments/${p.id}/${action}`); toast.success(action === "approve" ? "Approved — plan activated" : "Rejected"); load(); }
    catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6">
      <h3 className="text-xl font-bold">UPI Payments</h3>
      <p className="text-sm text-slate-500">Match the UTR with your UPI app / bank statement, then approve to activate the user's plan.</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {FILTERS.map(([k, l]) => <button key={k || "all"} onClick={() => setFilter(k)} data-testid={`payments-filter-${k || "all"}`} className={`px-3 py-1.5 rounded-full text-xs font-semibold ${filter === k ? "bg-[#0B132B] text-white" : "bg-slate-100 text-slate-600"}`}>{l}</button>)}
      </div>
      {rows.length === 0 ? <p className="mt-6 text-sm text-slate-500" data-testid="payments-empty">No payments here.</p> : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm" data-testid="admin-payments-table">
            <thead><tr className="text-left text-xs uppercase tracking-wider text-slate-400"><th className="py-2">User</th><th>Plan</th><th>Amount</th><th>UTR</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id} className="border-t border-slate-100" data-testid={`payment-row-${p.id}`}>
                  <td className="py-3 pr-3">{p.email}</td>
                  <td className="pr-3">{p.plan_name}</td>
                  <td className="pr-3 font-semibold">{rupees(p.amount)}</td>
                  <td className="pr-3 font-mono">{p.utr}</td>
                  <td className="pr-3 text-xs text-slate-500 whitespace-nowrap">{new Date(p.created_at).toLocaleString()}</td>
                  <td>
                    {p.status === "pending" ? (
                      <div className="flex gap-2">
                        <button onClick={() => decide(p, "approve")} data-testid={`approve-payment-${p.id}`} className="flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-full"><Check className="w-3.5 h-3.5" /> Approve</button>
                        <button onClick={() => decide(p, "reject")} data-testid={`reject-payment-${p.id}`} className="flex items-center gap-1 bg-slate-100 hover:bg-red-100 text-[#E50914] text-xs font-semibold px-3 py-1.5 rounded-full"><X className="w-3.5 h-3.5" /> Reject</button>
                      </div>
                    ) : <span className={`px-2 py-0.5 rounded-full text-xs font-semibold capitalize ${STATUS[p.status]}`}>{p.status}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
