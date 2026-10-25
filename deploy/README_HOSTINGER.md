# CreatorLive24/7 — Hostinger par deploy (VPS)

Ye app 3 hisson me chalta hai: website (React), server (Python FastAPI + ffmpeg live streaming) aur database (MongoDB).
Hostinger ka normal Web/Node.js hosting sirf website chala sakta hai, Python server aur MongoDB nahi.
Isliye **Hostinger VPS** (Ubuntu, kam se kam 2 vCPU / 4 GB RAM — KVM 2 ya upar) chahiye.

## Steps
1. Hostinger hPanel → VPS → OS: **Ubuntu 22.04 with Docker** chunein.
2. VPS me SSH karke code laayein:
   ```bash
   git clone <aapka-github-repo> creatorlive && cd creatorlive/deploy
   cp .env.example .env && nano .env   # values bharein (niche dekhein)
   docker compose up -d --build
   ```
3. Hostinger DNS Zone: `@` aur `www` ka **A record** VPS ke IP par karein (purane A/CNAME hata dein, CDN band karein).
4. HTTPS (SSL) ke liye VPS par Caddy/Certbot lagayein ya Hostinger VPS ka "Let's Encrypt" use karein. Camera/screen live streaming ke liye HTTPS zaroori hai.

## .env values
- `SITE_URL` – aapka domain, jaise `https://creatorlive247.com` (website isi par server ko call karegi)
- `EMERGENT_LLM_KEY` – Emergent Profile → Universal Key (video library storage ke liye)
- `CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` – Google login ke keys (Clerk dashboard se apne domain ke liye production keys)
- `ADMIN_EMAILS` – admin ka Gmail
