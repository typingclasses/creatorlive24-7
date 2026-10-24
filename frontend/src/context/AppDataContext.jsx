import { createContext, useCallback, useContext, useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "@clerk/react";
import { API } from "@/lib/api";

const AppDataContext = createContext(null);

export function AppDataProvider({ children }) {
  const { getToken, isSignedIn } = useAuth();
  const [settings, setSettings] = useState(null);
  const [me, setMe] = useState(null);

  const loadSettings = useCallback(() => axios.get(`${API}/settings`).then((r) => setSettings(r.data)).catch(() => {}), []);
  const loadMe = useCallback(async () => {
    if (!isSignedIn) return setMe(null);
    try {
      const token = await getToken();
      const { data } = await axios.get(`${API}/me`, { headers: { Authorization: `Bearer ${token}` } });
      setMe(data);
    } catch {}
  }, [getToken, isSignedIn]);

  useEffect(() => { loadSettings(); }, [loadSettings]);
  useEffect(() => { loadMe(); }, [loadMe]);

  return <AppDataContext.Provider value={{ settings, me, loadSettings, loadMe }}>{children}</AppDataContext.Provider>;
}

export const useAppData = () => useContext(AppDataContext);
