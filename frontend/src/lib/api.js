import { useCallback, useMemo } from "react";
import axios from "axios";
import { useAuth } from "@clerk/react";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const errMsg = (e) => {
  const d = e?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (e?.response?.status >= 500) return "Server is busy right now, please try again.";
  return e?.message || "Something went wrong";
};

export function useApi() {
  const { getToken } = useAuth();
  const req = useCallback(async (method, url, data, extra = {}) => {
    const token = await getToken();
    const { headers, ...rest } = extra;
    const res = await axios({ method, url: `${API}${url}`, data, headers: { Authorization: `Bearer ${token}`, ...headers }, ...rest });
    return res.data;
  }, [getToken]);
  return useMemo(() => ({
    get: (u, x) => req("get", u, undefined, x),
    post: (u, d, x) => req("post", u, d, x),
    put: (u, d, x) => req("put", u, d, x),
    patch: (u, d) => req("patch", u, d),
    del: (u) => req("delete", u),
    getToken,
  }), [req, getToken]);
}

export const formatSize = (b) => (b > 1e9 ? `${(b / 1e9).toFixed(2)} GB` : `${(b / 1e6).toFixed(1)} MB`);

export const formatDuration = (ms) => {
  const s = Math.max(0, Math.floor(ms / 1000));
  return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60].map((n) => String(n).padStart(2, "0")).join(":");
};
