"""Single-file MelodAI web app and ACE-Step API.

Run with ``python app.py`` from any platform after installing the dependencies
and placing ACE-Step in ``acestep-engine/upstream/``.
"""

from __future__ import annotations

import gc
import os
import threading
import uuid
import webbrowser
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parent
ENGINE_DIR = ROOT / "acestep-engine"
ENGINE_SOURCE_DIR = ENGINE_DIR / "upstream"
OUTPUT_DIR = ENGINE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pipeline = None
pipeline_lock = threading.Lock()
generation_lock = threading.Lock()
load_status = {"loading": False, "ready": False, "error": None}


class GenerateRequest(BaseModel):
    lyrics: Annotated[str, Field(min_length=1, max_length=12000)]
    genre: Annotated[str, Field(max_length=100)] = ""
    mood: Annotated[str, Field(max_length=100)] = ""
    theme: Annotated[str, Field(max_length=200)] = ""
    voice: Annotated[str, Field(max_length=20)] = ""
    duration: Annotated[float, Field(ge=15, le=240, allow_inf_nan=False)] = 60

    @field_validator("lyrics")
    @classmethod
    def lyrics_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Lyrics cannot be blank.")
        return value


def get_pipeline():
    global pipeline
    if pipeline is not None:
        return pipeline
    with pipeline_lock:
        if pipeline is None:
            load_status.update(loading=True, error=None)
            try:
                import sys

                for source_dir in (ENGINE_SOURCE_DIR, ENGINE_DIR):
                    if source_dir.is_dir():
                        sys.path.insert(0, str(source_dir))
                from acestep.pipeline_ace_step import ACEStepPipeline

                pipeline = ACEStepPipeline(
                    checkpoint_dir="",
                    dtype="float32",
                    overlapped_decode=True,
                )
                load_status["ready"] = True
            except Exception as exc:
                if isinstance(exc, ModuleNotFoundError) and exc.name == "acestep":
                    message = (
                        "ACE-Step is not installed in this Python environment. "
                        "Follow the platform-specific Install steps in README.md, "
                        "activate that environment, and run python app.py."
                    )
                    load_status["error"] = message
                    raise RuntimeError(message) from exc
                load_status["error"] = str(exc)
                raise
            finally:
                load_status["loading"] = False
    return pipeline


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


app = FastAPI(title="MelodAI", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.get("/health")
def health():
    return {"status": "ok", **load_status}


@app.get("/outputs/{filename}")
def get_audio(filename: str):
    if Path(filename).name != filename or not filename.endswith(".wav"):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    file_path = OUTPUT_DIR / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(file_path, media_type="audio/wav", filename=filename)


@app.post("/generate")
def generate(request: GenerateRequest):
    style = [request.genre.strip(), request.mood.strip(), request.theme.strip()]
    voice = request.voice.strip().lower()
    if voice in {"female", "male"}:
        style.insert(0, f"{voice} vocals, {voice} singer, {voice} voice")
    prompt = ", ".join(value for value in style if value) or "pop, upbeat"

    try:
        model = get_pipeline()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Model failed to load: {exc}") from exc

    destination = OUTPUT_DIR / f"{uuid.uuid4()}.wav"
    try:
        with generation_lock:
            generated = model(
                format="wav",
                audio_duration=request.duration,
                prompt=prompt,
                lyrics=request.lyrics.strip(),
                infer_step=20,
                guidance_scale=15.0,
                scheduler_type="euler",
                cfg_type="apg",
                omega_scale=10.0,
                save_path=str(destination),
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc
    finally:
        free_accelerator_memory()

    result_path = Path(generated[0]) if isinstance(generated, list) and generated else destination
    if not result_path.is_absolute():
        result_path = Path.cwd() / result_path
    try:
        result_path.resolve().relative_to(OUTPUT_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Audio was saved outside the output directory.") from exc
    if not result_path.is_file():
        raise HTTPException(status_code=500, detail="Generation did not produce an audio file.")
    return {"audio_url": f"/outputs/{result_path.name}", "tags": prompt}


HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MelodAI — Song Generator</title><style>
:root{color-scheme:dark;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#090910;color:#f7f4ff}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 50% -20%,#38205b 0,transparent 55%),#090910}.top{max-width:980px;margin:auto;padding:26px 28px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ffffff13}.brand{font-weight:750;letter-spacing:.04em}.health{font-size:.85rem;color:#b8aacb}.wrap{max-width:760px;margin:52px auto;padding:0 22px 60px}.intro{text-align:center;margin-bottom:34px}.intro h1{font-size:clamp(2rem,5vw,3.2rem);margin:0 0 10px;background:linear-gradient(90deg,#c084fc,#fb7185);color:transparent;background-clip:text}.intro p{color:#a9a1b8;margin:0}.card{padding:28px;border:1px solid #ffffff17;border-radius:22px;background:#11111bd9;box-shadow:0 20px 80px #0005}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.field{margin-bottom:20px}label{display:block;font-size:.76rem;text-transform:uppercase;letter-spacing:.09em;color:#aaa0b8;margin-bottom:8px}select,textarea,input{width:100%;border:1px solid #ffffff1e;border-radius:11px;background:#181823;color:#fff;padding:12px;font:inherit}textarea{min-height:190px;resize:vertical;line-height:1.55}input[type=range]{padding:8px 0;accent-color:#c084fc}.duration{display:flex;justify-content:space-between;color:#c9a8fb;font-size:.9rem}button{width:100%;border:0;border-radius:12px;padding:15px;background:linear-gradient(100deg,#7c3aed,#db2777);color:white;font-weight:700;font-size:1rem;cursor:pointer}button:disabled{opacity:.55;cursor:wait}.hint{color:#8e879c;font-size:.82rem;margin:8px 0 0}.error{display:none;margin:16px 0;padding:13px;border:1px solid #ef444466;background:#ef44441a;color:#fecaca;border-radius:10px}.player{display:none;margin-top:22px;padding:18px;border-radius:14px;background:#ffffff0a}.player audio{display:block;width:100%;margin:12px 0}.player a{color:#d8b4fe}.foot{text-align:center;color:#746e80;font-size:.8rem;margin-top:22px}@media(max-width:580px){.grid{grid-template-columns:1fr;gap:0}.wrap{margin-top:34px}.card{padding:20px}}
</style></head><body><header class="top"><div class="brand">✦ MELODAI</div><div id="health" class="health">Checking local engine…</div></header>
<main class="wrap"><section class="intro"><h1>Make a song your own.</h1><p>Write lyrics, set the vibe, and generate a sung track locally.</p></section><section class="card">
<div class="grid"><div class="field"><label for="genre">Genre</label><select id="genre"><option value="">Any genre</option><option>pop</option><option>hip-hop</option><option>r&amp;b</option><option>rock</option><option>jazz</option><option>electronic</option><option>classical</option><option>folk</option><option>metal</option><option>reggae</option></select></div>
<div class="field"><label for="mood">Mood</label><select id="mood"><option value="">Any mood</option><option>upbeat</option><option>melancholic</option><option>energetic</option><option>calm</option><option>romantic</option><option>dark</option><option>hopeful</option><option>dreamy</option></select></div>
<div class="field"><label for="theme">Theme</label><select id="theme"><option value="">Any theme</option><option>love</option><option>heartbreak</option><option>friendship</option><option>nature</option><option>journey</option><option>nostalgia</option><option>rebellion</option><option>hope</option></select></div>
<div class="field"><label for="voice">Voice</label><select id="voice"><option value="">Any voice</option><option value="female">Female</option><option value="male">Male</option></select></div></div>
<div class="field"><div class="duration"><label for="duration">Song length</label><span id="duration-label">60 sec</span></div><input id="duration" type="range" min="30" max="240" step="15" value="60"></div>
<div class="field"><label for="lyrics">Lyrics</label><textarea id="lyrics" maxlength="12000" placeholder="[verse]&#10;Write your lyrics here…&#10;&#10;[chorus]&#10;Add your chorus"></textarea><p class="hint">Structure lyrics with tags such as [verse], [chorus], and [bridge].</p></div>
<div id="error" class="error" role="alert"></div><button id="generate">Generate song</button><div class="player" id="player"><strong>Your song is ready</strong><audio id="audio" controls></audio><a id="download" download>Download WAV</a></div></section><div class="foot">Runs on your computer with ACE-Step. Your lyrics stay local.</div></main>
<script>
const $=id=>document.getElementById(id), slider=$('duration');slider.addEventListener('input',()=> $('duration-label').textContent=slider.value+' sec');
async function health(){try{const r=await fetch('/health',{cache:'no-store'});if(!r.ok)throw Error();$('health').textContent='Local server connected'}catch{$('health').textContent='Local server unavailable'}}health();setInterval(health,5000);
$('generate').addEventListener('click',async()=>{const lyrics=$('lyrics').value.trim(),err=$('error'),btn=$('generate'),player=$('player');err.style.display='none';player.style.display='none';if(!lyrics){err.textContent='Add lyrics before generating your song.';err.style.display='block';return}btn.disabled=true;btn.textContent='Generating… this can take a few minutes';try{const response=await fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lyrics,genre:$('genre').value,mood:$('mood').value,theme:$('theme').value,voice:$('voice').value,duration:Number(slider.value)})});let data;try{data=await response.json()}catch{throw Error('The server returned an unreadable response.')}if(!response.ok)throw Error(data.detail||'Song generation failed.');const audioUrl=data.audio_url;$('audio').src=audioUrl;$('audio').load();$('download').href=audioUrl;player.style.display='block';player.scrollIntoView({behavior:'smooth',block:'nearest'})}catch(e){err.textContent=e.message;err.style.display='block'}finally{btn.disabled=false;btn.textContent='Generate song'}});
</script></body></html>'''


if __name__ == "__main__":
    host = os.environ.get("MELODAI_HOST", "127.0.0.1")
    port = int(os.environ.get("MELODAI_PORT", "8001"))
    url = f"http://{host}:{port}"
    threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=host, port=port)
