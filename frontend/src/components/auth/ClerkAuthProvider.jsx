import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ClerkProvider, ClerkFailed } from "@clerk/react";

const appearance = { variables: { colorPrimary: "#E50914", fontFamily: "Plus Jakarta Sans, sans-serif", borderRadius: "0.75rem" } };

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const fetchConfig = async () => {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  try {
    const res = await fetch(`${BACKEND_URL}/api/clerk/config`, { signal: ctrl.signal, cache: "no-store" });
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
};

const Notice = ({ slow, onRetry }) => (
  <div data-testid="auth-connecting" style={{ minHeight: "60vh", display: "grid", placeItems: "center", padding: 24, textAlign: "center", fontFamily: "Plus Jakarta Sans, sans-serif" }}>
    <div>
      <div style={{ width: 36, height: 36, margin: "0 auto 16px", border: "4px solid #E2E8F0", borderTopColor: "#E50914", borderRadius: "50%", animation: "spin 0.9s linear infinite" }} />
      <style>{"@keyframes spin{to{transform:rotate(360deg)}}"}</style>
      <p style={{ fontWeight: 700, color: "#0B132B" }}>CreatorLive24/7</p>
      <p style={{ color: "#64748B", fontSize: 14 }}>{slow ? "Internet slow lag raha hai, connect kar rahe hain…" : "Loading…"}</p>
      {slow && <button data-testid="auth-retry-button" onClick={onRetry} style={{ marginTop: 12, background: "#E50914", color: "#fff", border: 0, borderRadius: 999, padding: "10px 22px", fontWeight: 600 }}>Retry</button>}
    </div>
  </div>
);

export default function ClerkAuthProvider({ children }) {
  const navigate = useNavigate();
  const [config, setConfig] = useState(null);
  const [attempts, setAttempts] = useState(0);
  const [run, setRun] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async (attempt = 0) => {
      try {
        const cfg = await fetchConfig();
        if (cfg.enabled) return cancelled || setConfig(cfg);
      } catch {}
      if (cancelled) return;
      setAttempts(attempt + 1);
      setTimeout(() => !cancelled && load(attempt + 1), Math.min(1000 * (attempt + 1), 5000));
    };
    load();
    return () => { cancelled = true; };
  }, [run]);

  const retry = useCallback(() => { setAttempts(0); setRun((r) => r + 1); }, []);

  if (!config) return <Notice slow={attempts >= 3} onRetry={retry} />;
  return (
    <ClerkProvider
      publishableKey={config.publishable_key}
      proxyUrl={config.proxy_url || undefined}
      appearance={appearance}
      routerPush={(to) => navigate(to)}
      routerReplace={(to) => navigate(to, { replace: true })}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/"
      signUpFallbackRedirectUrl="/"
      afterSignOutUrl="/"
    >
      <ClerkFailed>
        <div data-testid="auth-failed" style={{ background: "#FEF2F2", color: "#B91C1C", padding: "10px 16px", textAlign: "center", fontSize: 14 }}>
          Login service load nahi hua. <button onClick={() => window.location.reload()} style={{ textDecoration: "underline", fontWeight: 600 }}>Page reload karein</button>
        </div>
      </ClerkFailed>
      {children}
    </ClerkProvider>
  );
}
