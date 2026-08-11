# Build native macOS launcher app

## One-time setup:
```bash
pip install py2app
python3 setup.py py2app
```

This creates **MelodAI-Launcher.app** — a real executable macOS application with:
- ✅ No visible source code
- ✅ Native app icon and behavior
- ✅ Auto-starts backend on click
- ✅ Opens app in browser

Then just **double-click MelodAI-Launcher.app** to launch everything!

## After building:
- The `.app` file will be in the `dist/` folder
- Move it to the repo root if desired
- Double-click to run (no terminal needed)
