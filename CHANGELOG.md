# Changelog

## 0.1.0 - clean baseline

### Added

- New repository structure with `src/`, tests, docs, and sample data notes.
- GUI entry point via `python start.py`.
- CLI entry point via `python start.py --input ... --output ...`.
- CSV export.
- GeoJSON export.
- JSON summary report.
- Optional list of files without GPS metadata.
- ExifTool-first extraction mode for better HEIF/HEIC/RAW support.
- Pillow/pillow-heif fallback for common image formats.
- Strict `.gitignore` to avoid committing private images, outputs, archives, and temporary folders.
