import { useEffect, useState } from "react";
import { Users, UserCheck, Crown, Clock, Film, Radio } from "lucide-react";
import { useApi } from "@/lib/api";

const CARDS = [["users", "Total users", Users], ["active_users", "Active users", UserCheck], ["paid_users", "On a paid plan", Crown],
  ["pending_payments", "Payments to verify", Clock], ["videos", "Videos uploaded", Film], ["streams", "Streams done", Radio]];

export default function AdminOverview() {
  const api = useApi();
  const [s, setS] = useState(null);
  useEffect(() => { api.get("/admin/stats").then(setS).catch(() => {}); }, [api]);
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
      {CARDS.map(([k, label, I]) => (
        <div key={k} className="bg-white border border-slate-200 rounded-2xl p-6" data-testid={`admin-stat-${k}`}>
          <I className="w-5 h-5 text-[#1D4ED8]" />
          <p className="mt-4 font-display text-3xl font-extrabold">{s ? s[k] : "–"}</p>
          <p className="text-sm text-slate-500">{label}</p>
        </div>
      ))}
    </div>
  );
}
