# Mitotic spindle tool
An image analysis Python GUI application for use in Dr. Elting's lab at NCSU.

# Authors
- [Kergan Sanderson](https://github.com/virtualkergan/)
- [Joe Lannan](https://github.com/joe-lannan)

# Install
## Packaged Executables
[Get the latest release here](https://github.com/eltinglab/mitotic-spindle-tool/releases/latest)

## Manual Install
### Requirements: [Python](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) and [Git](https://git-scm.com/downloads)

open terminal

clone this repo `git clone https://github.com/eltinglab/mitotic-spindle-tool`

cd into this repo `cd mitotic-spindle-tool`

create a python envirnoment using your favorite way to do that. [Micromamba](https://micromamba.readthedocs.io/en/latest/) recomended.

with the activated environment, install the requirements with `pip install -r requirements.txt`

run `python src/spindleGUI.py`


# New Features:

Hotkeys for faster data processing

Click on a column to show a plot of the data

Click row to select that frame to edit

# Development

## Version Management

This project uses centralized version management. The version is defined once in `src/version.py` and automatically used by all other components.

### Updating Version

Use the provided script to update versions:

```bash
# Set specific version
python3 update_version.py 1.2.0

# Bump version semantically
python3 update_version.py --bump patch   # 1.1.0 → 1.1.1
python3 update_version.py --bump minor   # 1.1.0 → 1.2.0  
python3 update_version.py --bump major   # 1.1.0 → 2.0.0
```

This automatically updates:
- `src/version.py` (source of truth)
- `pyproject.toml` (for compatibility)
- GUI displays the version automatically via import

## Building

Use the cross-platform build script:

```bash
python3 build.py
```

This creates executables for your platform and attempts to create AppImage on Linux.
