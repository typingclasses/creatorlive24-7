# CreatorLive24/7 — PRD

## Original problem
Live streaming website "CreatorLive24/7" (Tripoliya, Patna, Bihar). Users live stream to YouTube & Facebook. Setup: Step 1 stream keys, Step 2 stream source, Step 3 Go Live Studio. Login with Google.
User choices: real streaming to YouTube/Facebook; videos saved in cloud library; Video Library section.

## Architecture
- Auth: Emergent-managed Clerk (Google sign-in)
- Backend FastAPI: destinations (stream keys per user), videos (Emergent Object Storage + local cache), streams (ffmpeg via imageio-ffmpeg → RTMP tee to all enabled platforms), WebSocket /api/ws/live for browser camera/screen (MediaRecorder webm → ffmpeg stdin)
- Frontend React: Landing, Dashboard, Setup wizard (3 steps), Video Library

## Implemented (2026-10-23)
- Landing page with user banner, features, 3 steps, footer with address
- Google login, protected pages
- Step 1 YouTube/Facebook keys (server URL editable), Step 2 camera / screen / video (upload or pick from library) + toolbar (tips, orientation, HD/FHD, 30/60fps, replay loop), Step 3 studio with preview, Go Live, LIVE badge, timer, End stream, error display
- Library: upload, preview, delete, stream
- Dashboard: status, quick actions, stream history
- Tested: 24/24 backend tests, frontend flows pass

## 2026-10-23 (iteration 2)
- Fixed: bundled ffmpeg couldn't resolve hostnames -> added local DNS/TLS relay (backend/relay.py); real YouTube stream verified with user's key
- Friendly 422 errors for rejected keys, failed starts not logged in history

- Facebook rtmps verified live with user key; YouTube+Facebook together verified; failed platform warning; stream keys masked in logs

- Library: chunked uploads (20MB parts, up to 5GB per video) fixing long-format upload failure; auto Long/Short detection + tabs + switch; Range-enabled preview with 6h signed play URL

## Backlog
- P1: Scheduled 24/7 playlists (multiple videos in rotation), auto-restart if platform connection drops
- P1: Video seek/Range support in preview, thumbnails
- P2: Monetization guide, Instagram/X, overlays/watermark, live chat
