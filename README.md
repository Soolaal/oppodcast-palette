# Oppodcast Studio

**Oppodcast Studio** is a lightweight, professional desktop soundboard designed for live podcasting and streaming. Built with Python and CustomTkinter, it provides a stable, zero-latency environment for playing jingles and managing your show.

![Status](https://img.shields.io/badge/Status-Production_Ready-success)
![Python](https://img.shields.io/badge/Python-3.10+-blue)

## Features

- **30-Slot Sound Grid:** Drag & drop interface to assign sounds.
- **Live Safety Mode:** "Edit Mode" switch prevents accidental deletions or moves during the show.
- **Studio Monitor:** Integrated Clock and Stopwatch for precise timing.
- **Player Bar:** Visual progress bar with elapsed/remaining time.
- **Integrated Notes:** A dedicated tab for your script or show notes (auto-saved).
- **Always on Top:** Keeps the window floating above OBS or your browser.
- **Presets System:** Create and switch between multiple shows (JSON based).
- **Multi-language:** English and French support.

## Installation & Usage

### Option A: Standalone Executable (Windows)
1. Download the latest `OppodcastStudio.exe` release.
2. Create a folder named `Oppodcast Studio` on your desktop.
3. Place the `.exe` inside.
4. Create a folder named `presets` next to the executable.
5. Run the app!

### Option B: Running from Source
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Soolaal/oppodcast.git
   cd oppodcast
```

2. **Install dependencies:**

```bash
pip install customtkinter pygame
```

3. **Run the studio:**

```bash
python OppodcastStudio.py
```


## How to Compile (.exe)

If you want to build the executable yourself:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile OppodcastStudio.py
```

The output file will be in the `dist/` folder.

## Project Structure

- `OppodcastStudio.py` : Main application source code.
- `presets/` : Folder storing your sound grids (JSON files).
- `notes.txt` : Auto-generated file storing your current notes.


## Controls

- **Left Click:** Play sound (Live Mode) / Select sound (Edit Mode).
- **Edit Switch:** Toggle between playing sounds and organizing them.
- **Always on Top:** Keeps the window in the foreground.


