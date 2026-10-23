import { Link } from "react-router-dom";

export const Logo = ({ dark = false }) => (
  <Link to="/" data-testid="brand-logo-link" className="flex items-center gap-2.5 group">
    <span className="relative grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-[#1D4ED8] to-[#0B132B] shadow-md transition-transform duration-300 group-hover:-rotate-6">
      <svg viewBox="0 0 24 24" className="w-4 h-4 fill-white ml-0.5"><path d="M8 5v14l11-7z" /></svg>
      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#E50914] live-dot ring-2 ring-white" />
    </span>
    <span className={`font-display font-extrabold text-xl tracking-tight ${dark ? "text-white" : "text-[#0B132B]"}`}>
      CreatorLive<span className="text-[#1D4ED8]">24/7</span>
    </span>
  </Link>
);
