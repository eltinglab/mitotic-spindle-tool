# Manual Version Management & Release Workflow

This repository uses **manual version bumping only**. Maintainers must manually edit version files to trigger releases.

## 🚀 How to Release a New Version

### Step 1: Manual Version Bump
Choose one of these methods to update the version:

#### Method A: Direct Edit
```bash
# Edit src/version.py directly
# Change: __version__ = "1.1.2"
# To:     __version__ = "1.1.3"
```

#### Method B: Update Script
```bash
# Use the helper script
python3 update_version.py 1.1.3

# Or use bump commands
python3 update_version.py --bump patch   # 1.1.2 → 1.1.3
python3 update_version.py --bump minor   # 1.1.2 → 1.2.0  
python3 update_version.py --bump major   # 1.1.2 → 2.0.0
```

### Step 2: Create Pull Request
```bash
# Create branch for version bump
git checkout -b version-bump-v1.1.3
git add src/version.py pyproject.toml
git commit -m "Bump version to v1.1.3"
git push origin version-bump-v1.1.3

# Create PR on GitHub with title like: "Bump version to v1.1.3"
```

### Step 3: Automatic Release (After PR Merge)
Once the version bump PR is merged to main:

1. **Auto-tag Creation** (`auto-release-on-version-bump.yml`)
   - Detects version change in `src/version.py`
   - Compares with latest git tag
   - Creates new tag (e.g., `v1.1.3`)

2. **Release Build** (`release.yml`)
   - Triggered by new tag
   - Builds executables for all platforms:
     - Windows: `mitotic-spindle-tool.exe`
     - Linux: `mitotic-spindle-tool-linux.tar.gz` + `mitotic-spindle-tool.AppImage`
     - macOS: `mitotic-spindle-tool-macos.dmg`
   - Creates GitHub release with all artifacts

## 📋 Version Bump Guidelines

### Semantic Versioning
- **Patch** (1.1.2 → 1.1.3): Bug fixes, small improvements
- **Minor** (1.1.2 → 1.2.0): New features, backward compatible
- **Major** (1.1.2 → 2.0.0): Breaking changes, API changes

### When to Bump
- Fix a bug → patch bump
- Add new feature → minor bump  
- Change UI significantly → minor bump
- Remove features or change APIs → major bump

## 🛠️ Repository Configuration

### Branch Protection Rules
- ✅ Requires pull requests for changes
- ✅ Requires signed commits  
- ✅ Prevents direct pushes to main

### Workflow Status
- ✅ **Auto Tag and Release on Manual Version Change** - Creates tags when version.py changes
- ✅ **Release Build** - Builds and publishes releases when tags are created
- ❌ **Manual Version Bump Helper** - Removed (use manual editing)
- ❌ **Auto Version Bump on Merge** - Removed (manual only)
- ❌ **Semantic Version Bump** - Removed (manual only)

## 📁 Version Files

- **Primary**: `src/version.py` - Single source of truth for version
- **Secondary**: `pyproject.toml` - Automatically synced by update_version.py
- **Helper**: `update_version.py` - Version management utility script

## 🎯 Current Version

Check current version:
```bash
python3 update_version.py
# or
python3 -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)"
```

## 🔧 Troubleshooting

### Tag Already Exists Error
If the workflow fails with "tag already exists":
```bash
# Check existing tags
git tag --list

# If you need to re-release, delete the tag first:
git tag -d v1.1.3              # Delete locally
git push origin --delete v1.1.3  # Delete from remote (careful!)
```

### No Release Created
Common issues:
- Version in `src/version.py` wasn't actually changed
- Tag already exists for that version
- Workflow didn't detect the change (check file path: `src/version.py`)

### Manual Release Creation
If automated release fails, create manually:
```bash
# Create tag manually
git tag -a v1.1.3 -m "Release v1.1.3"
git push origin v1.1.3

# Or use GitHub UI: Releases → Create a new release
```

## 📝 Workflow Summary

**Simple Process:**
1. 👨‍💻 **Maintainer edits** `src/version.py` manually
2. 📝 **Create PR** with version change  
3. ✅ **Merge PR** to main
4. 🤖 **Auto-tag created** by GitHub Actions
5. 🚀 **Release built** automatically with all platform binaries

**No automated bumping, no complex workflows - just manual version changes triggering releases.**
