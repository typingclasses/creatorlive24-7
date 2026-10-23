import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useUser } from "@clerk/react";
import { Radio, Upload, KeyRound, History, Youtube, Facebook } from "lucide-react";
import { useApi, formatDuration } from "@/lib/api";
import { useStudio } from "@/context/StudioContext";
import { LiveTimer } from "@/components/wizard/LiveTimer";

const Action = ({ to, icon: I, t, s, id }) => (
  <Link to={to} data-testid={id} className="group flex items-center gap-4 bg-white border border-slate-200 rounded-2xl p-5 hover:border-[#E50914] transition-colors">
    <span className="grid place-items-center w-11 h-11 rounded-xl bg-slate-100 group-hover:bg-[#E50914] transition-colors"><I className="w-5 h-5 text-[#0B132B] group-hover:text-white" /></span>
    <div><p className="font-semibold">{t}</p><p className="text-xs text-slate-500">{s}</p></div>
  </Link>
);

export default function Dashboard() {
  const { user } = useUser();
  const api = useApi();
  const { status } = useStudio();
  const [history, setHistory] = useState([]);
  const [dest, setDest] = useState(null);

  useEffect(() => {
    api.get("/streams/history").then(setHistory).catch(() => {});
    api.get("/destinations").then(setDest).catch(() => {});
  }, [api, status.live]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-400 font-semibold">Welcome back</p>
      <h1 className="mt-2 text-4xl sm:text-5xl font-extrabold tracking-tight" data-testid="dashboard-greeting">{user?.firstName || "Creator"}'s Dashboard</h1>
      <div className="mt-10 grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 bg-[#0B132B] text-white rounded-3xl p-8" data-testid="dashboard-status-card">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Stream Status</p>
            {status.live ? (
              <span className="flex items-center gap-1.5 bg-[#10B981] text-white text-xs font-bold px-3 py-1 rounded-full"><span className="w-2 h-2 rounded-full bg-white live-dot" /> Online</span>
            ) : <span className="bg-white/10 text-xs font-bold px-3 py-1 rounded-full">Offline</span>}
          </div>
          {status.live ? (
            <div className="mt-6">
              <p className="text-slate-400 text-sm">{status.title} → {status.platforms?.join(" + ")}</p>
              <LiveTimer startedAt={status.started_at} className="text-5xl mt-2" />
            </div>
          ) : <p className="mt-6 text-2xl font-display font-semibold">You have no active streams.</p>}
          <div className="mt-8 flex gap-3 text-sm">
            <span className="flex items-center gap-1.5"><Youtube className="w-4 h-4 text-[#E50914]" /> {dest?.youtube?.enabled ? "Connected" : "Not set"}</span>
            <span className="flex items-center gap-1.5"><Facebook className="w-4 h-4 text-[#60A5FA]" /> {dest?.facebook?.enabled ? "Connected" : "Not set"}</span>
          </div>
        </div>
        <div className="lg:col-span-5 grid gap-3">
          <Action to="/setup?step=1" icon={KeyRound} t="Stream Keys" s="Step 1 · add YouTube / Facebook keys" id="quick-stream-keys" />
          <Action to="/setup?step=2" icon={Radio} t="Start New Stream" s="Camera, screen or library video" id="quick-start-stream" />
          <Action to="/library" icon={Upload} t="Upload Video" s="Add a new video to your library" id="quick-upload-video" />
        </div>
      </div>
      <div className="mt-10 bg-white border border-slate-200 rounded-3xl p-8">
        <h3 className="text-xl font-bold flex items-center gap-2"><History className="w-5 h-5" /> Recent streams</h3>
        {history.length === 0 ? <p className="mt-4 text-sm text-slate-500" data-testid="history-empty">No streams yet.</p> : (
          <ul className="mt-4 divide-y divide-slate-100" data-testid="history-list">
            {history.map((h) => (
              <li key={h.id} className="py-3 flex items-center justify-between text-sm">
                <span className="font-medium">{h.title}<span className="text-slate-400"> · {h.platforms.join(", ")}</span></span>
                <span className="font-mono text-slate-500">{new Date(h.started_at).toLocaleString()} · {formatDuration(new Date(h.ended_at) - new Date(h.started_at))}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
