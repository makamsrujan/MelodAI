"""Streamlit frontend for MelodAI

This app starts the local FastAPI backend (via ./start.sh) if it's not
running, waits for /health to be ready, and provides a simple UI to
POST /generate and play/download the returned WAV.

Usage:
  pip install streamlit requests
  streamlit run app.py

Notes:
- The ACE-Step model is heavy and (per README) expects Apple Silicon (MPS).
  This app simply launches the repository's start.sh which will create the
  venv and run the backend. First run may take several minutes.
- You can set the environment variable MELODAI_API to a public backend URL
  (e.g. https://abcd1234.ngrok.io) if you run the backend elsewhere.
"""

import streamlit as st
import subprocess
import requests
import time
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()
BACKEND_ENV = os.environ.get("MELODAI_API")
BACKEND_URL = BACKEND_ENV or "http://localhost:8000"
START_CMD = ["bash", "./start.sh"]
START_TIMEOUT = int(os.environ.get("MELODAI_START_TIMEOUT", "600"))


def backend_running(timeout=2):
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=timeout)
        return r.ok
    except Exception:
        return False


def start_backend(timeout=START_TIMEOUT):
    """Start the bundled start.sh in the repo root and wait for /health.

    Returns: subprocess.Popen object for the background process.
    Raises RuntimeError on failure.
    """
    log_dir = REPO_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "backend.log"

    # If start.sh is not present, try running the acestep-engine start directly
    start_sh = REPO_ROOT / "start.sh"
    if not start_sh.exists():
        raise RuntimeError("start.sh not found in repo root")

    # Launch start.sh via bash in the repo root. Redirect stdout/stderr to a log file.
    lf = open(str(log_file), "ab")
    proc = subprocess.Popen(START_CMD, cwd=str(REPO_ROOT), stdout=lf, stderr=subprocess.STDOUT)

    # Wait for health endpoint
    deadline = time.time() + timeout
    while time.time() < deadline:
        if backend_running(timeout=2):
            return proc
        time.sleep(1)

    raise RuntimeError(f"Backend did not become ready within {timeout} seconds. See {log_file}")


st.set_page_config(page_title="MelodAI — Streamlit", layout="centered")
st.title("MelodAI — AI Music Generator (Streamlit)")

st.markdown(
    """
- This Streamlit app will attempt to start the MelodAI backend (ACE‑Step) using the repo's `start.sh`.
- First runs will download and install the model and dependencies and may take several minutes.
- If you already have a backend running somewhere, set the environment variable `MELODAI_API`
  to its base URL (for example `https://abcd1234.ngrok.io`) before starting Streamlit.
"""
)

# Start backend automatically if needed
if "backend_proc" not in st.session_state:
    st.session_state.backend_proc = None

if BACKEND_ENV:
    st.info(f"Using external backend at {BACKEND_URL}")
else:
    if backend_running():
        st.success("Backend already running at http://localhost:8000")
        st.session_state.backend_proc = None
    else:
        with st.spinner("Starting MelodAI backend (this may take a few minutes)..."):
            try:
                proc = start_backend()
                st.session_state.backend_proc = proc
                st.success("Backend is ready at http://localhost:8000")
            except Exception as e:
                st.error(f"Failed to start backend: {e}")
                with st.expander("Backend logs (last 200 lines)"):
                    log_path = REPO_ROOT / "logs" / "backend.log"
                    if log_path.exists():
                        try:
                            with open(log_path, "rb") as f:
                                data = f.read()
                                # show last 200 lines
                                lines = data.decode(errors="replace").splitlines()
                                tail = "\n".join(lines[-200:])
                                st.code(tail)
                        except Exception as e:
                            st.write("Could not read log file:", e)
                    else:
                        st.write("No log file yet. start.sh may not have started.")

# Input fields
col1, col2 = st.columns(2)
with col1:
    genre = st.selectbox("Genre", ["", "pop", "hip-hop", "r&b", "rock", "jazz", "electronic", "classical", "folk", "metal", "reggae"])
    mood = st.selectbox("Mood", ["", "upbeat", "melancholic", "energetic", "calm", "romantic", "dark", "hopeful", "angry", "dreamy", "intense"])
with col2:
    theme = st.selectbox("Theme", ["", "love", "heartbreak", "friendship", "nature", "journey", "nostalgia", "rebellion", "hope", "loss", "celebration"])
    voice = st.selectbox("Voice", ["", "female", "male"])

duration = st.slider("Duration (s)", 30, 240, 60, 15)
lyrics = st.text_area("Lyrics (use [verse], [chorus], ...)", height=300)

col_generate = st.container()

if col_generate.button("Generate song"):
    if not lyrics.strip():
        st.error("Please enter some lyrics.")
    elif not backend_running():
        st.error("Backend is not ready. If you just started it, wait a bit and try again. See logs in /logs/backend.log")
    else:
        with st.spinner("Generating — this can take 1–3 minutes for a short clip..."):
            payload = {
                "lyrics": lyrics,
                "genre": genre,
                "mood": mood,
                "theme": theme,
                "voice": voice,
                "duration": duration,
            }
            try:
                r = requests.post(f"{BACKEND_URL}/generate", json=payload, timeout=1200)
                r.raise_for_status()
                data = r.json()
                audio_path = data.get("audio_url")
                if not audio_path:
                    st.error("Backend did not return audio_url in response.")
                else:
                    audio_url = audio_path if audio_path.startswith("http") else f"{BACKEND_URL}{audio_path}"
                    # fetch audio bytes
                    ar = requests.get(audio_url, timeout=120)
                    ar.raise_for_status()
                    audio_bytes = ar.content
                    st.success("Generation complete")
                    st.audio(audio_bytes, format="audio/wav")
                    st.markdown(f"[Download audio]({audio_url})")
            except Exception as e:
                st.error(f"Generation failed: {e}")

# Footer: show backend status and controls
st.sidebar.title("MelodAI backend")
if backend_running():
    st.sidebar.success(f"Backend OK — {BACKEND_URL}/health")
else:
    st.sidebar.error("Backend not reachable")

st.sidebar.markdown("---")
if st.sidebar.button("Open API docs"):
    st.sidebar.info(f"Open {BACKEND_URL}/docs in your browser")

st.sidebar.markdown("Logs live in ./logs/backend.log")

# Keep a note about shutting down the background process when the Streamlit app stops
st.sidebar.markdown(
    """
If Streamlit started the backend for you, the backend process keeps running independently.
To stop it, find the pid in `ps` or reboot your machine. If you want a nicer service/daemon,
consider using launchd/systemd to run `./start.sh` on boot.
"""
)
