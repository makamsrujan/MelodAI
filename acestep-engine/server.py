"""
MelodAI backend — local ACE-Step inference (sings the lyrics).
Run from inside the acestep-engine venv:
    uvicorn server:app --port 8000
"""
import os
import gc
import uuid
import threading
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(
    title="MelodAI",
    description="AI Music Generator - Generate full songs with sung vocals from lyrics + genre/mood/theme using ACE-Step running locally on your Mac's GPU",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

APP_HTML = Path(__file__).parent.parent / "MelodAI.html"


@app.get("/")
def index():
    return FileResponse(APP_HTML)

# Lazily-loaded singleton pipeline (loading downloads ~3.5GB on first run).
_pipeline = None
_pipeline_lock = threading.Lock()
_load_status = {"loading": False, "ready": False, "error": None}


def get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    with _pipeline_lock:
        if _pipeline is not None:
            return _pipeline
        _load_status["loading"] = True
        try:
            # float32 is REQUIRED on Apple MPS — float16 triggers slow CPU
            # fallbacks and memory thrashing (10-100x slower). overlapped_decode
            # speeds up the final audio decode stage at no quality cost.
            from acestep.pipeline_ace_step import ACEStepPipeline
            _pipeline = ACEStepPipeline(
                checkpoint_dir="",
                dtype="float32",
                overlapped_decode=True,
            )
            _load_status["ready"] = True
        except Exception as e:
            _load_status["error"] = str(e)
            raise
        finally:
            _load_status["loading"] = False
    return _pipeline


class GenerateRequest(BaseModel):
    """Request body for music generation"""
    lyrics: str = ""
    genre: str = ""
    mood: str = ""
    theme: str = ""
    voice: str = ""
    duration: float = 60.0


def build_tags(req: GenerateRequest) -> str:
    parts = []
    # Lead with the voice cue and reinforce it — a single trailing tag is too
    # weak and ACE-Step often defaults to a male voice otherwise.
    voice = req.voice.strip().lower()
    if voice in ("male", "female"):
        parts += [f"{voice} vocals", f"{voice} singer", f"{voice} voice"]
    parts += [p.strip() for p in [req.genre, req.mood, req.theme] if p.strip()]
    return ", ".join(parts) if parts else "pop, upbeat"


@app.post("/generate")
def generate_music(req: GenerateRequest):
    """Generate a song with sung vocals from lyrics and preferences"""
    tags = build_tags(req)
    lyrics = req.lyrics.strip() or "[inst]"
    duration = max(15.0, min(240.0, float(req.duration)))

    try:
        pipeline = get_pipeline()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model failed to load: {e}")

    filename = f"{uuid.uuid4()}.wav"
    dest = OUTPUT_DIR / filename

    try:
        paths = pipeline(
            format="wav",
            audio_duration=duration,
            prompt=tags,
            lyrics=lyrics,
            infer_step=20,          # fewer steps = faster; 20 keeps good quality
            guidance_scale=15.0,
            scheduler_type="euler",
            cfg_type="apg",
            omega_scale=10.0,
            save_path=str(dest),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")
    finally:
        # MPS does not release GPU memory between runs, so it accumulates and
        # forces swap (each song gets slower). Clearing the cache after every
        # generation keeps memory flat and timings consistent.
        free_accelerator_memory()

    out = paths[0] if isinstance(paths, list) and paths else str(dest)
    out_name = Path(out).name
    return {"audio_url": f"/outputs/{out_name}", "tags": tags}


def free_accelerator_memory():
    gc.collect()
    try:
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


@app.get("/health")
def health():
    """Check if backend and model are ready"""
    return {"status": "ok", **_load_status}
