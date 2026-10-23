// Uploads a video in small chunks so large (long format) files get past proxy size/time limits.
export async function uploadVideo(api, file, onProgress) {
  if (!file.type.startsWith("video/")) throw new Error("Only video files are allowed");
  if (file.size > 5 * 1024 ** 3) throw new Error("Video must be under 5 GB");
  const { upload_id, chunk_size } = await api.post("/uploads", { filename: file.name, size: file.size, content_type: file.type });
  const total = Math.ceil(file.size / chunk_size);
  for (let i = 0; i < total; i++) {
    const blob = file.slice(i * chunk_size, Math.min(file.size, (i + 1) * chunk_size));
    for (let attempt = 1; ; attempt++) {
      try {
        await api.put(`/uploads/${upload_id}/chunks/${i}`, blob, {
          headers: { "Content-Type": "application/octet-stream" },
          onUploadProgress: (e) => onProgress?.(Math.min(99, Math.round(((i * chunk_size + e.loaded) / file.size) * 100))),
        });
        break;
      } catch (e) {
        if (attempt >= 4 || e?.response?.status === 400 || e?.response?.status === 404) throw e;
        await new Promise((r) => setTimeout(r, 1500 * attempt));
      }
    }
    onProgress?.(Math.min(99, Math.round(((i + 1) / total) * 100)));
  }
  return api.post(`/uploads/${upload_id}/complete`);
}

export const formatLength = (sec) => {
  if (sec == null) return "";
  const s = Math.round(sec);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return (h ? `${h}:${String(m).padStart(2, "0")}` : `${m}`) + `:${String(r).padStart(2, "0")}`;
};
