# Mitotic spindle tool
An image analysis Python GUI application for use in Dr. Elting's lab at NCSU.

# Authors
- [Kergan Sanderson](https://github.com/virtualkergan/)
- [Joe Lannan](https://github.com/joe-lannan)

## Quick Start - Pre-built Executables

**Download the latest release for your platform:**
- 🪟 **Windows**: Download the `.exe` file from [Releases](https://github.com/eltinglab/mitotic-spindle-tool/releases)
- 🍎 **macOS**: Download the `.dmg` file from [Releases](https://github.com/eltinglab/mitotic-spindle-tool/releases)
- 🐧 **Linux**: Download the `.tar.gz` or `.AppImage` file from [Releases](https://github.com/eltinglab/mitotic-spindle-tool/releases)

No installation required - just download and run!

# Install from Source
### Requirements: [Python](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) and [Git](https://git-scm.com/downloads)

open terminal

clone this repo `git clone https://github.com/eltinglab/mitotic-spindle-tool`

cd into this repo `cd mitotic-spindle-tool`

create a python envirnoment using your favorite way to do that. [Micromamba](https://micromamba.readthedocs.io/en/latest/) recomended.

with the activated environment, install the requirements with `pip install -r requirements.txt`

run `python src/spindleGUI.py`

## Building Executables

To build platform-specific executables yourself:

```bash
python build.py
```

This will create:
- **Windows**: `dist/mitotic-spindle-tool.exe`
- **macOS**: `dist/mitotic-spindle-tool-macos.dmg` 
- **Linux**: `dist/mitotic-spindle-tool-linux.tar.gz` and `dist/mitotic-spindle-tool.AppImage`

# New Features:

Hotkeys for faster data processing

Click on a column to show a plot of the data

Click row to select that frame to edit

Run all button that probably will make a mess
