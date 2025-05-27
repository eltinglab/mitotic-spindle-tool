# CI/CD Workflows

This repository includes several GitHub Actions workflows for automated building, testing, and releasing of the Mitotic Spindle Tool.

## Workflows Overview

### 1. Build and Test (`build-and-test.yml`)
**Triggers**: Push to main/develop branches, Pull Requests
- Tests the code on multiple Python versions (3.9, 3.10, 3.11)
- Builds executables for Windows, Linux, and macOS
- Runs linting and import tests
- Uploads build artifacts for testing

### 2. PR Build Check (`pr-build.yml`)
**Triggers**: Pull Request events (opened, updated, reopened)
- Builds executables for all platforms on PR changes
- Creates downloadable artifacts for testing PR changes
- Posts build status comments on PRs with download links
- Artifacts are retained for 30 days

### 3. Release Build (`release.yml`)
**Triggers**: Version tags (v*), Published releases
- Builds production executables for all platforms
- Creates platform-specific packages (ZIP for Windows, tar.gz for Unix)
- Uploads packages as GitHub release assets
- Creates AppImage for Linux (if tools available)

### 4. Version Management (`version.yml`)
**Triggers**: Manual workflow dispatch
- Automatically bumps version numbers
- Updates version in multiple files (setup.py, pyproject.toml, spindleGUI.py)
- Creates git tags and GitHub releases
- Supports major, minor, patch bumps or specific version numbers

## Supported Platforms

| Platform | Executable | Package Format | Notes |
|----------|------------|----------------|-------|
| **Windows** | `mitotic-spindle-tool.exe` | ZIP archive | Includes batch launcher |
| **Linux** | `mitotic-spindle-tool` | tar.gz + AppImage | Includes shell launcher |
| **macOS** | `mitotic-spindle-tool` | tar.gz | Includes shell launcher |

## Using the Workflows

### For Contributors

#### Testing Pull Requests
1. Create a pull request against `main` or `develop`
2. The PR Build workflow automatically runs
3. Check the workflow status in the PR
4. Download test artifacts from the workflow run
5. A comment will be posted with build results and download links

#### Testing Locally Built Executables
```bash
# Download artifacts from GitHub Actions
# Extract the package for your platform
# Test the executable before merging
```

### For Maintainers

#### Creating Releases

**Option 1: Automatic Version Bump**
1. Go to Actions → Version Management → Run workflow
2. Choose version bump type (patch/minor/major) or specify exact version
3. Workflow will update version numbers and create a draft release
4. Release Build workflow will automatically trigger and upload executables

**Option 2: Manual Release**
1. Manually update version numbers in:
   - `setup.py`
   - `pyproject.toml` 
   - `src/spindleGUI.py`
2. Create and push a version tag: `git tag v1.0.3 && git push origin v1.0.3`
3. Release Build workflow will automatically trigger

#### Managing Releases
- Draft releases are created automatically
- Review and edit release notes before publishing
- Once published, executables are immediately available for download

## Workflow Configuration

### Secrets Required
- `GITHUB_TOKEN` (automatically provided by GitHub)

### Optional Enhancements
You may want to add these secrets for enhanced functionality:

- **Code Signing**: Add certificates for signing executables
- **Notarization**: Add Apple Developer credentials for macOS notarization
- **Distribution**: Add credentials for package managers (Homebrew, Chocolatey, etc.)

### Customizing Workflows

#### Adding New Platforms
To add support for additional platforms, update the matrix in relevant workflows:

```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        platform: linux
      - os: windows-latest
        platform: windows
      - os: macos-latest
        platform: macos
      # Add new platforms here
```

#### Modifying Build Process
- Edit `build.py` to change the build process
- Update PyInstaller spec file for executable configuration
- Modify package creation steps in workflows

#### Changing Python Versions
Update the Python version matrix in `build-and-test.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12']
```

## Artifacts and Downloads

### PR Artifacts
- **Retention**: 30 days
- **Naming**: `pr-{PR_NUMBER}-{PLATFORM}-build`
- **Contents**: Executable + launcher + AppImage (Linux)

### Release Artifacts
- **Retention**: Permanent (GitHub release assets)
- **Naming**: `mitotic-spindle-tool-{PLATFORM}.{extension}`
- **Contents**: Production-ready packages

### Build Reports
- Available in PR comments
- Include file sizes, build status, and download links
- Help reviewers test changes before merging

## Troubleshooting Workflows

### Common Issues

#### Build Failures
1. Check the workflow logs for specific error messages
2. Verify all dependencies are listed in `requirements.txt`
3. Test the build process locally using `python build.py`

#### Missing Artifacts
1. Ensure the build completed successfully
2. Check if the executable was created in the expected location
3. Verify upload steps completed without errors

#### Version Conflicts
1. Ensure version numbers are consistent across all files
2. Check that git tags follow the expected format (`v1.0.0`)
3. Verify no duplicate tags exist

### Manual Intervention

#### Force Rebuild
If you need to rebuild without code changes:
1. Go to Actions → Select workflow → Run workflow
2. Choose the appropriate branch
3. Monitor the build progress

#### Debug Mode
To enable debug output in builds:
1. Edit `mitotic-spindle-tool.spec`
2. Set `debug=True` and `console=True`
3. Commit and push changes

## Best Practices

### For Contributors
- Test builds locally before creating PRs
- Keep PRs focused to make build testing easier
- Check PR comments for build status and test downloads

### For Maintainers
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Test release candidates before publishing
- Keep release notes informative and user-friendly
- Monitor workflow status and fix issues promptly

### Security Considerations
- Workflows only trigger on protected branches and PRs
- No secrets are exposed in public logs
- Artifacts are only accessible to repository collaborators
- Consider code signing for production releases
