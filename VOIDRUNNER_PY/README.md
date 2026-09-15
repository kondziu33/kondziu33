# VOIDRUNNER — Python 3D Edition

3D third-person action platformer / shooter / roguelite built with Python + Ursina (Panda3D).

## Windows 11

Install Python 3.12 x64, then double-click `build_windows.bat`. The script creates a local virtual environment, installs dependencies, and builds `dist\\MyGame.exe`.

For source mode:

```powershell
py -3 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe run.py
```

GitHub Actions workflow `.github/workflows/build-windows.yml` builds the Windows executable automatically and uploads it as `VOIDRUNNER-Windows-x64`.

## Structure

- `run.py` — entry point
- `voidrunner/game.py` — player, combat, enemies, bosses, procedural levels, UI, save/load
- `voidrunner/data/content.py` — weapons, items, potions, enemies, levels and achievements
- `VOIDRUNNER.spec` — PyInstaller packaging
- `build_windows.bat` / `build_windows.ps1` — local Windows build helpers
- `assets/` — replaceable content directory

The current edition uses procedural geometry so it can launch without an external asset pack. Production 3D models, animations and audio can be added under `assets/` without changing the data-driven content definitions.
