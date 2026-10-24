import { MapPin, Zap, ShieldCheck, TrendingUp, Coins, Youtube, Facebook, Instagram, Twitter, Phone, Mail, MessageCircle } from "lucide-react";
import { Logo } from "@/components/Logo";
import { useAppData } from "@/context/AppDataContext";

const SOCIAL = [["youtube", Youtube, "YouTube"], ["facebook", Facebook, "Facebook"], ["instagram", Instagram, "Instagram"], ["twitter", Twitter, "X (Twitter)"]];

const SupportBlock = ({ s }) => (
  <div className="space-y-2 text-sm" data-testid="footer-support">
    <p className="font-display font-bold">Support Us</p>
    {s.support_text && <p className="text-slate-400 max-w-xs">{s.support_text}</p>}
    {s.mobile && <a href={`tel:${s.mobile}`} data-testid="footer-mobile" className="flex items-center gap-2 hover:text-[#FFB703]"><Phone className="w-4 h-4" /> {s.mobile}</a>}
    {s.whatsapp && <a href={`https://wa.me/${s.whatsapp.replace(/\D/g, "")}`} target="_blank" rel="noreferrer" data-testid="footer-whatsapp" className="flex items-center gap-2 hover:text-[#FFB703]"><MessageCircle className="w-4 h-4" /> WhatsApp</a>}
    {s.support_email && <a href={`mailto:${s.support_email}`} data-testid="footer-email" className="flex items-center gap-2 hover:text-[#FFB703]"><Mail className="w-4 h-4" /> {s.support_email}</a>}
  </div>
);

const strip = [
  { icon: Zap, t: "Fast Setup", s: "Start in minutes" },
  { icon: ShieldCheck, t: "Secure & Reliable", s: "Your data, our priority" },
  { icon: TrendingUp, t: "Build Your Audience", s: "More views, more growth" },
  { icon: Coins, t: "Monetize Smarter", s: "Turn views into income" },
];

export default function Footer() {
  const { settings } = useAppData();
  const s = settings || { social: {}, address: "Tripoliya, Patna, Bihar", tagline: "Your Content. Always On." };
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
          <p className="text-sm text-slate-400 max-w-sm">{s.tagline} Stream live to YouTube and Facebook from your browser.</p>
        </div>
        <div className="flex items-center gap-3" data-testid="footer-address">
          <MapPin className="w-6 h-6 text-[#E50914]" />
          <div><p className="font-semibold">{s.address}</p><p className="text-xs text-slate-400">Our Business Address</p></div>
        </div>
        <SupportBlock s={s} />
        <div className="flex flex-wrap gap-2 text-sm" data-testid="footer-social">
          {SOCIAL.map(([k, I, label]) => s.social?.[k] ? (
            <a key={k} href={s.social[k]} target="_blank" rel="noreferrer" data-testid={`footer-social-${k}`} className="flex items-center gap-1.5 bg-white/5 hover:bg-white/15 px-3 py-2 rounded-full transition-colors"><I className="w-4 h-4" /> {label}</a>
          ) : null)}
        </div>
      </div>
      <p className="text-center text-xs text-slate-500 pb-6">© {new Date().getFullYear()} {settings?.site_name || "CreatorLive24/7"} · {s.address}</p>
    </footer>
  );
}
