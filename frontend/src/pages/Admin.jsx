import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAppData } from "@/context/AppDataContext";
import AdminOverview from "@/components/admin/AdminOverview";
import AdminUsers from "@/components/admin/AdminUsers";
import AdminPlans from "@/components/admin/AdminPlans";
import AdminPayments from "@/components/admin/AdminPayments";
import AdminSettings from "@/components/admin/AdminSettings";

const TABS = [["overview", "Overview", AdminOverview], ["users", "Users", AdminUsers], ["plans", "Plans & Offers", AdminPlans],
  ["payments", "Payments", AdminPayments], ["settings", "Main Page Settings", AdminSettings]];

export default function Admin() {
  const { me } = useAppData();
  if (!me) return <Loader2 className="w-6 h-6 animate-spin mx-auto mt-20" />;
  if (!me.is_admin) return <Navigate to="/dashboard" replace />;
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold">Admin Panel</p>
      <h1 className="mt-2 text-4xl sm:text-5xl font-extrabold tracking-tight">Manage CreatorLive24/7</h1>
      <Tabs defaultValue="overview" className="mt-8">
        <TabsList className="flex-wrap h-auto bg-white border border-slate-200 rounded-2xl p-1.5">
          {TABS.map(([k, label]) => <TabsTrigger key={k} value={k} data-testid={`admin-tab-${k}`} className="rounded-xl data-[state=active]:bg-[#0B132B] data-[state=active]:text-white">{label}</TabsTrigger>)}
        </TabsList>
        {TABS.map(([k, , C]) => <TabsContent key={k} value={k} className="mt-6"><C /></TabsContent>)}
      </Tabs>
    </div>
  );
}
