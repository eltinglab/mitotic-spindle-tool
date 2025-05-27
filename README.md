# Mitotic spindle tool
An image analysis Python GUI application for use in Dr. Elting's lab at NCSU.

[![Build and Test](https://github.com/eltinglab/mitotic-spindle-tool/actions/workflows/build-and-test.yml/badge.svg)](https://github.com/eltinglab/mitotic-spindle-tool/actions/workflows/build-and-test.yml)
[![Release Build](https://github.com/eltinglab/mitotic-spindle-tool/actions/workflows/release.yml/badge.svg)](https://github.com/eltinglab/mitotic-spindle-tool/actions/workflows/release.yml)

## Downloads

### Pre-built Executables
**Recommended for most users** - No Python installation required!

**[Latest Release](https://github.com/eltinglab/mitotic-spindle-tool/releases/latest)**

| Platform | Download | Notes |
|----------|----------|-------|
| **Windows** | `mitotic-spindle-tool-windows.zip` | Extract and run `mitotic-spindle-tool.exe` |
| **Linux** | `mitotic-spindle-tool-linux.tar.gz` | Extract and run `./mitotic-spindle-tool` |
| **Linux** | `mitotic-spindle-tool.AppImage` | Single file, just download and run |
| **macOS** | `mitotic-spindle-tool-macos.tar.gz` | Extract and run `./mitotic-spindle-tool` |

### Development/Source Installation
If you want to modify the code or use the latest development version:

# Authors
- [Kergan Sanderson](https://github.com/virtualkergan/)
- [Joe Lannan](https://github.com/joe-lannan)

# Run with system python
### Requirements: [Python](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html) and [Git](https://git-scm.com/downloads)

open terminal

clone this repo `git clone https://github.com/eltinglab/mitotic-spindle-tool`

cd into this repo `cd mitotic-spindle-tool`

create a python envirnoment using your favorite way to do that. [Micromamba](https://micromamba.readthedocs.io/en/latest/) recomended.

with the activated environment, install the requirements with `pip install -r requirements.txt`

run `python src/spindleGUI.py`


# New Features:

- **Coordinate Preview**: View spindle coordinates in original image space
- **Hotkeys for faster data processing**: Navigate and process data without using mouse
- **Interactive data visualization**: Click on a column to show a plot of the data
- **Frame selection**: Click row to select that frame to edit
- **Batch processing**: Run all button for processing multiple frames with current settings
- **Manual override**: Manually adjust spindle pole positions when automatic detection fails

## For Developers

### Building from Source
See [BUILD.md](BUILD.md) for detailed build instructions.

Quick build for current platform:
```bash
python build.py
```

### CI/CD Workflows
This project uses GitHub Actions for automated building and releasing. See [WORKFLOWS.md](WORKFLOWS.md) for details on:
- Automated builds on pull requests
- Cross-platform release creation
- Version management
- Artifact distribution

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Create a pull request
5. Automated builds will test your changes on all platforms
6. Download build artifacts from the PR to test executables
