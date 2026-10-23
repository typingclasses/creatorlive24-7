import { useEffect, useState } from "react";
import { formatDuration } from "@/lib/api";

export const LiveTimer = ({ startedAt, className = "" }) => {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  return <span data-testid="live-timer" className={`font-mono font-semibold tabular-nums ${className}`}>{formatDuration(startedAt ? now - new Date(startedAt).getTime() : 0)}</span>;
};
