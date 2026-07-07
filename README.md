# MelodAI — AI Music Generator

Generate **full songs with sung vocals** from lyrics + genre/mood/theme, using
**ACE-Step (3.5B)** running **locally** on your Mac's GPU (Apple MPS). Free, no API
keys, no rate limits, no broken demo spaces.

## Stack
- **Model**: `ACE-Step/ACE-Step-v1-3.5B` — runs locally, sings your lyrics
- **Backend**: FastAPI (`acestep-engine/server.py`) — loads the model once, exposes `/generate`
- **Frontend**: single openable `MelodAI.html` (no build step)

## Prerequisites
- **Apple Silicon Mac** (M1/M2/M3/M4/M5). 16GB+ unified memory recommended.
- **Python 3.11** — `brew install python@3.11`
- **ffmpeg** — `brew install ffmpeg`
- ~8GB free disk (model is cached to `~/.cache/ace-step/`)

---

## Setup (one time)

This repo tracks only our own files (`server.py`, `analyze_pitch.py`, the app,
and docs). The ACE-Step engine itself is **not** committed — clone it into
`acestep-engine/` so it sits alongside our `server.py`:

```bash
# from the repo root, pull the ACE-Step engine into acestep-engine/
git clone https://github.com/ace-step/ACE-Step.git /tmp/ace-step
cp -R /tmp/ace-step/. acestep-engine/        # merges engine next to our server.py

cd acestep-engine
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements-server.txt       # torchcodec (needed to write audio)
```

The 3.5B model (~7GB) downloads automatically on the **first** generation.

---

## Run

**1. Start the backend** (keep this terminal open):
```bash
cd acestep-engine
source venv/bin/activate
uvicorn server:app --port 8000
```
Or just run `./start.sh` from the project root.

Check it: `curl http://localhost:8000/health` → `{"status":"ok","ready":...}`

**2. Open the app:** go to **http://localhost:8000** in your browser
(or double-click **`MelodAI.html`** — both work).
The page auto-detects the backend and shows a green "Backend ready" dot.

Interactive API docs available at **http://localhost:8000/docs**.

---

## How It Works
1. The page POSTs `{lyrics, genre, mood, theme, duration}` to `/generate`.
2. The backend builds a style prompt (e.g. `"pop, upbeat, love"`) and feeds it +
   your lyrics to the local ACE-Step pipeline.
3. ACE-Step runs the diffusion process on the GPU (MPS) and **sings the lyrics**.
4. The 48kHz stereo WAV is saved to `acestep-engine/outputs/` and streamed back
   to the in-page player (with a Download button).

## Performance (Apple Silicon)
- First run: a few minutes (one-time model download + load).
- After that: ~1 minute for a 30s clip; scales with duration and `infer_step`.
- The model stays loaded in the server process, so back-to-back songs are fast.

## Tips
- Use `[verse]`, `[chorus]`, `[bridge]` tags in lyrics — ACE-Step respects song structure.
- Genre/mood/theme become the musical style prompt. Leave them blank for a default vibe.
- Tune quality/speed via `infer_step` in `server.py` (default 27).
