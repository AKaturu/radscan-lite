# Desktop Releases

GitHub Actions can build downloadable desktop artifacts for users who do not want to install Python.

## Release Artifacts

| Platform | Artifact | Contents |
|---|---|---|
| Windows | `radscan-lite-windows.zip` | `RadScanLite.exe` |
| macOS | `radscan-lite-macos.dmg` | `RadScanLite.app` |
| Linux | `radscan-lite-linux.tar.gz` | `RadScanLite` executable |

The desktop launcher starts the Streamlit app locally in the user's browser. It does not send DICOM data to a hosted service.

## Build Locally

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[packaging]"
```

| Platform | Command |
|---|---|
| Windows | `packaging\build_windows.bat` |
| macOS | `bash packaging/build_macos.sh` |
| Linux | `bash packaging/build_linux.sh` |

Build outputs are written to `dist/`.

## CI Release Build

The workflow in `.github/workflows/desktop-release.yml` runs on:

- manual `workflow_dispatch`
- tags that match `v*`

For a public release, create a tag such as `v0.1.0`, let the workflow produce the artifacts, then attach the artifacts to a GitHub Release.
