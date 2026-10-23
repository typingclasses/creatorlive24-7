import { Link } from "react-router-dom";
import { Radio, Library, Repeat, KeyRound, MonitorUp, Clapperboard, ArrowRight, Youtube, Facebook } from "lucide-react";

const BANNER = "https://customer-assets-7cd3h4nn.emergentagent.net/job_3bf591bf-31b9-4281-8286-96cc6e1ae707/artifacts/aa52c68221b69745_CreatorLive24_7%20Streaming%20Platform%20Banner%20%281%29.webp";

const features = [
  { icon: Radio, c: "bg-[#E50914]", t: "Live Streaming", s: "Camera or screen, straight from your browser to YouTube & Facebook." },
  { icon: Library, c: "bg-[#1D4ED8]", t: "Video Library", s: "Upload videos once to the cloud and stream them whenever you want." },
  { icon: Repeat, c: "bg-[#10B981]", t: "Loop Videos", s: "Replay a library video on repeat — runs on our server, even if you close the tab." },
];

const steps = [
  { icon: KeyRound, n: "01", t: "Stream Keys", s: "Paste your YouTube and/or Facebook stream key." },
  { icon: MonitorUp, n: "02", t: "Stream Source", s: "Pick your camera, screen or a video from the library." },
  { icon: Clapperboard, n: "03", t: "Go Live Studio", s: "Preview, hit Go Live and watch the timer run." },
];

export default function Landing() {
  return (
    <div>
      <section className="relative overflow-hidden grid-bg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 lg:pt-24">
          <div className="max-w-3xl rise">
            <span className="inline-flex items-center gap-2 bg-[#E50914] text-white text-xs font-bold px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-white live-dot" /> LIVE 24/7
            </span>
            <h1 className="mt-6 text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.02] text-[#0B132B]">
              Go Live Faster. <span className="text-[#1D4ED8]">Stream Smarter.</span> Grow <span className="relative">24/7.<span className="absolute left-0 -bottom-1 h-2 w-full bg-[#FFB703] -z-10 rounded" /></span>
            </h1>
            <p className="mt-6 text-base md:text-lg text-slate-600 max-w-xl">Your Content. Always On. Set up your stream key, pick a source and broadcast to YouTube and Facebook in three simple steps.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/sign-in" data-testid="hero-get-started-button" className="group inline-flex items-center gap-2 bg-[#E50914] text-white font-semibold px-7 py-3.5 rounded-full hover:bg-[#C80711] transition-colors">
                Start streaming with Google <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Link>
              <a href="#how" data-testid="hero-how-it-works-link" className="inline-flex items-center gap-2 bg-white border border-slate-200 text-[#0B132B] font-semibold px-7 py-3.5 rounded-full hover:border-[#0B132B] transition-colors">How it works</a>
            </div>
            <div className="mt-8 flex items-center gap-5 text-sm text-slate-500">
              <span className="flex items-center gap-1.5"><Youtube className="w-5 h-5 text-[#E50914]" /> YouTube</span>
              <span className="flex items-center gap-1.5"><Facebook className="w-5 h-5 text-[#1877F2]" /> Facebook</span>
            </div>
          </div>
          <div className="mt-14 rise" style={{ animationDelay: ".15s" }}>
            <img src={BANNER} alt="CreatorLive24/7 banner" data-testid="hero-banner-image" className="w-full rounded-3xl shadow-[0_30px_80px_-30px_rgba(11,19,43,.45)] border border-white" />
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 grid md:grid-cols-3 gap-6">
        {features.map(({ icon: I, c, t, s }, i) => (
          <div key={t} className="rise bg-white border border-slate-200 rounded-3xl p-8 hover:-translate-y-1 hover:shadow-xl transition-[transform,box-shadow] duration-300" style={{ animationDelay: `${i * 0.08}s` }}>
            <span className={`grid place-items-center w-12 h-12 rounded-2xl ${c}`}><I className="w-6 h-6 text-white" /></span>
            <h3 className="mt-6 text-xl font-bold">{t}</h3>
            <p className="mt-2 text-slate-600 text-sm leading-relaxed">{s}</p>
          </div>
        ))}
      </section>

      <section id="how" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-[#0B132B] rounded-[2rem] p-8 md:p-14 text-white">
          <p className="text-xs uppercase tracking-[0.25em] text-[#FFB703] font-semibold">Setup Live Streaming</p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold max-w-xl">Three steps between you and your audience.</h2>
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            {steps.map(({ icon: I, n, t, s }) => (
              <div key={n} className="border border-white/10 rounded-2xl p-6 bg-white/[0.03]">
                <div className="flex items-center justify-between"><I className="w-7 h-7 text-[#60A5FA]" /><span className="font-mono text-slate-500">{n}</span></div>
                <h3 className="mt-6 text-lg font-semibold">Step {Number(n)} · {t}</h3>
                <p className="mt-2 text-sm text-slate-400">{s}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
