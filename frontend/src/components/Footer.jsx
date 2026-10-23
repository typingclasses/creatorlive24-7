import { MapPin, Zap, ShieldCheck, TrendingUp, Coins, Youtube, Facebook } from "lucide-react";
import { Logo } from "@/components/Logo";

const strip = [
  { icon: Zap, t: "Fast Setup", s: "Start in minutes" },
  { icon: ShieldCheck, t: "Secure & Reliable", s: "Your data, our priority" },
  { icon: TrendingUp, t: "Build Your Audience", s: "More views, more growth" },
  { icon: Coins, t: "Monetize Smarter", s: "Turn views into income" },
];

export default function Footer() {
  return (
    <footer className="mt-24 bg-[#0B132B] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-2 lg:grid-cols-4 gap-6 py-10 border-b border-white/10">
        {strip.map(({ icon: I, t, s }) => (
          <div key={t} className="flex items-start gap-3">
            <I className="w-7 h-7 text-[#60A5FA] shrink-0" />
            <div><p className="font-display font-bold">{t}</p><p className="text-sm text-slate-400">{s}</p></div>
          </div>
        ))}
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col md:flex-row gap-8 md:items-center justify-between">
        <div className="space-y-3">
          <Logo dark />
          <p className="text-sm text-slate-400 max-w-sm">Your Content. Always On. Stream live to YouTube and Facebook from your browser.</p>
        </div>
        <div className="flex items-center gap-3" data-testid="footer-address">
          <MapPin className="w-6 h-6 text-[#E50914]" />
          <div><p className="font-semibold">Tripoliya, Patna, Bihar</p><p className="text-xs text-slate-400">Our Business Address</p></div>
        </div>
        <div className="flex gap-3 text-sm">
          <span className="flex items-center gap-1.5 bg-white/5 px-3 py-2 rounded-full"><Youtube className="w-4 h-4 text-[#E50914]" /> YouTube</span>
          <span className="flex items-center gap-1.5 bg-white/5 px-3 py-2 rounded-full"><Facebook className="w-4 h-4 text-[#60A5FA]" /> Facebook</span>
        </div>
      </div>
      <p className="text-center text-xs text-slate-500 pb-6">© {new Date().getFullYear()} CreatorLive24/7 · Patna, Bihar</p>
    </footer>
  );
}
