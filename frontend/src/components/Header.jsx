import { NavLink, Link } from "react-router-dom";
import { Show, UserButton } from "@clerk/react";
import { Logo } from "@/components/Logo";
import { useStudio } from "@/context/StudioContext";

const links = [
  { to: "/dashboard", label: "Dashboard", id: "nav-dashboard" },
  { to: "/setup", label: "Go Live", id: "nav-setup" },
  { to: "/library", label: "Video Library", id: "nav-library" },
];

const LiveBadge = () => {
  const { status } = useStudio();
  if (!status.live) return null;
  return (
    <Link to="/setup?step=3" data-testid="header-live-badge" className="flex items-center gap-1.5 bg-[#E50914] text-white text-xs font-bold px-3 py-1.5 rounded-full">
      <span className="w-2 h-2 rounded-full bg-white live-dot" /> ON AIR
    </Link>
  );
};

export default function Header() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        <Logo />
        <Show when="signed-in">
          <nav className="hidden md:flex items-center gap-1">
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} data-testid={l.id}
                className={({ isActive }) => `px-4 py-2 rounded-full text-sm font-semibold transition-colors ${isActive ? "bg-[#0B132B] text-white" : "text-slate-600 hover:bg-slate-100 hover:text-[#0B132B]"}`}>
                {l.label}
              </NavLink>
            ))}
          </nav>
        </Show>
        <div className="flex items-center justify-end gap-3 md:min-w-[220px]">
          <Show when="signed-in">
            <LiveBadge />
            <div data-testid="user-menu"><UserButton /></div>
          </Show>
          <Show when="signed-out">
            <Link to="/sign-in" data-testid="header-signin-button"
              className="flex items-center gap-2 bg-[#0B132B] text-white text-sm font-semibold px-5 py-2.5 rounded-full hover:bg-[#E50914] transition-colors">
              Sign in with Google
            </Link>
          </Show>
        </div>
      </div>
      <Show when="signed-in">
        <nav className="md:hidden flex gap-1 px-4 pb-2 overflow-x-auto">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} data-testid={`${l.id}-mobile`}
              className={({ isActive }) => `px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap ${isActive ? "bg-[#0B132B] text-white" : "text-slate-600 bg-slate-100"}`}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </Show>
    </header>
  );
}
