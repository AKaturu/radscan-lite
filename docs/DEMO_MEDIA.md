# Demo Media

The repository demo assets are generated from a synthetic DICOM preflight scenario. They are intended for public GitHub documentation and do not include patient data.

## Files

- `demo_assets/demo.gif` - README animation
- `demo_assets/demo.mp4` - downloadable demo clip
- `demo_assets/demo-poster.png` - static preview frame
- `demo_assets/*.png` - existing static walkthrough screenshots

## Regenerate

```bash
python -m pip install -e ".[media]"
python scripts/generate_demo_media.py
```

The generator renders a stable final frame and duplicates it for the GIF/MP4 so the demo does not flicker on GitHub.
