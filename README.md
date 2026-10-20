# MelodAI

MelodAI is a single-file Python app that opens a local browser interface for generating songs from lyrics and style choices. The interface, web server, API, playback, and WAV download handling are all contained in `app.py`; no separate HTML, frontend build, or platform-specific launcher is needed.

The Python app is portable across Windows, macOS, and Linux. Song generation also requires ACE-Step and PyTorch dependencies supported by the host OS and hardware. A compatible GPU/accelerator is recommended; CPU-only generation can be very slow. ACE-Step downloads its model weights the first time you generate a song.

## Requirements

- Python 3.11 (recommended for the ACE-Step version used here)
- Git
- Several gigabytes of disk space for ACE-Step and model weights
- A browser

## Install

Run these commands from the repository folder. Keep the ACE-Step source in `acestep-engine/upstream/`; that local dependency is ignored by Git and does not add another application implementation to this repository.

```text
git clone https://github.com/ace-step/ACE-Step.git acestep-engine/upstream
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```bat
.venv\Scripts\activate.bat
```

**macOS or Linux**

```bash
source .venv/bin/activate
```

Then, on any platform, install the model and app dependencies:

```text
python -m pip install --upgrade pip
python -m pip install -e acestep-engine/upstream
python -m pip install -r requirements.txt
```

If an ACE-Step dependency needs an operating-system-specific installation, use the instructions from the [ACE-Step repository](https://github.com/ace-step/ACE-Step).

## Run

With the virtual environment active, run:

```text
python app.py
```

MelodAI opens in your default browser at [http://127.0.0.1:8001](http://127.0.0.1:8001). Keep the Python process running while using the app; press Ctrl+C in its terminal to stop it.

The default port can be changed with `MELODAI_PORT`:

```powershell
$env:MELODAI_PORT = "8002"; python app.py
```

```bash
MELODAI_PORT=8002 python app.py
```

## Features

- Generates sung music from lyrics, genre, mood, theme, voice, and duration.
- Plays generated audio in the browser and offers a WAV download.
- Keeps generated files in the ignored local `acestep-engine/outputs/` folder.
- Provides a health endpoint at `/health` and API documentation at `/docs`.
- Validates lyrics and duration and prevents simultaneous calls into the shared model.

## Repository files

- `app.py` — the single Python application, including its embedded interface.
- `requirements.txt` — app-specific Python dependencies.
- `README.md` — installation and usage instructions.
- `.gitignore` — excludes local environments, ACE-Step source, model weights, and generated audio.
