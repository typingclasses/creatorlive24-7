import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useApi, errMsg } from "@/lib/api";

const UserRow = ({ u, plans, onChange }) => (
  <tr className="border-t border-slate-100" data-testid={`admin-user-row-${u.user_id}`}>
    <td className="py-3 pr-3">
      <p className="font-medium" data-testid={`admin-user-email-${u.user_id}`}>{u.email || "—"}</p>
      <p className="text-xs text-slate-500">{u.name}{u.is_admin && <span className="ml-2 text-[#1D4ED8] font-semibold">Admin</span>}</p>
    </td>
    <td className="py-3 pr-3 min-w-[180px]">
      <Select value={u.plan_valid ? u.plan_id : "none"} onValueChange={(v) => onChange(u, { plan_id: v === "none" ? "" : v })}>
        <SelectTrigger className="h-9" data-testid={`admin-user-plan-select-${u.user_id}`}><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="none">No plan</SelectItem>
          {plans.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
        </SelectContent>
      </Select>
      {u.plan_valid && <p className="text-[11px] text-slate-500 mt-1">till {new Date(u.plan_expires_at).toLocaleDateString()}</p>}
    </td>
    <td className="py-3 pr-3 text-xs text-slate-500 whitespace-nowrap">{new Date(u.created_at).toLocaleDateString()}</td>
    <td className="py-3">
      <div className="flex items-center gap-2">
        <Switch checked={u.active !== false} disabled={u.is_admin} onCheckedChange={(v) => onChange(u, { active: v })} data-testid={`admin-user-active-switch-${u.user_id}`} />
        <span className={`text-xs font-semibold ${u.active !== false ? "text-emerald-600" : "text-[#E50914]"}`}>{u.active !== false ? "Active" : "Deactivated"}</span>
      </div>
    </td>
  </tr>
);

export default function AdminUsers() {
  const api = useApi();
  const [users, setUsers] = useState(null);
  const [plans, setPlans] = useState([]);
  const [q, setQ] = useState("");
  const load = useCallback(() => api.get("/admin/users").then(setUsers).catch((e) => toast.error(errMsg(e))), [api]);
  useEffect(() => { load(); api.get("/admin/plans").then(setPlans).catch(() => {}); }, [load, api]);

  const change = async (u, patch) => {
    try { await api.patch(`/admin/users/${u.user_id}`, patch); toast.success("User updated"); load(); }
    catch (e) { toast.error(errMsg(e)); }
  };
  const shown = (users || []).filter((u) => `${u.email} ${u.name}`.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6">
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <h3 className="text-xl font-bold">Users {users && <span className="text-slate-400 font-normal">({users.length})</span>}</h3>
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search email or name" className="pl-9" data-testid="admin-user-search-input" />
        </div>
      </div>
      {!users ? <Loader2 className="w-5 h-5 animate-spin mx-auto my-10" /> : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm" data-testid="admin-users-table">
            <thead><tr className="text-left text-xs uppercase tracking-wider text-slate-400"><th className="py-2">Email</th><th>Subscription plan</th><th>Joined</th><th>Status</th></tr></thead>
            <tbody>{shown.map((u) => <UserRow key={u.user_id} u={u} plans={plans} onChange={change} />)}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
