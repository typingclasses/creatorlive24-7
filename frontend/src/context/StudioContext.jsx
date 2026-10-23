import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/react";
import { API } from "@/lib/api";
import axios from "axios";

const StudioContext = createContext(null);

export function StudioProvider({ children }) {
  const { getToken, isSignedIn } = useAuth();
  const [source, setSourceState] = useState(null); // {type, stream?, video?}
  const [settings, setSettings] = useState({ quality: "720p", fps: 30, loop: true, landscape: true });
  const [status, setStatus] = useState({ live: false });
  const streamRef = useRef(null);

  const setSource = useCallback((next) => {
    if (streamRef.current && streamRef.current !== next?.stream) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    streamRef.current = next?.stream || null;
    setSourceState(next);
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const token = await getToken();
      const { data } = await axios.get(`${API}/streams/status`, { headers: { Authorization: `Bearer ${token}` } });
      setStatus(data);
    } catch {}
  }, [getToken]);

  useEffect(() => {
    if (!isSignedIn) return;
    refreshStatus();
    const t = setInterval(refreshStatus, 4000);
    return () => clearInterval(t);
  }, [isSignedIn, refreshStatus]);

  return (
    <StudioContext.Provider value={{ source, setSource, settings, setSettings, status, refreshStatus }}>
      {children}
    </StudioContext.Provider>
  );
}

export const useStudio = () => useContext(StudioContext);
