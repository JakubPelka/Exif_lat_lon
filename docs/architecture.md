# Architecture

## Goal

Extract GPS coordinates from local image files and export them to CSV and GeoJSON without modifying the source files.

## Design

The project has three layers:

```text
start.py
  ├── GUI path: exif_lat_lon.gui
  └── CLI path: exif_lat_lon.cli
          └── core logic: exif_lat_lon.core
```

## Core module

`src/exif_lat_lon/core.py` contains:

- supported file extensions
- folder scanning
- ExifTool availability detection
- ExifTool metadata extraction
- Pillow/pillow-heif fallback extraction
- GPS DMS to decimal conversion
- CSV writing
- GeoJSON writing
- summary report writing

## Extractor strategy

### `auto`

Default mode.

1. Use ExifTool if available.
2. Fall back to Pillow/pillow-heif if ExifTool is not available.

### `exiftool`

Best mode for broad format support, especially HEIF/HEIC and camera RAW.

Requires the external `exiftool` executable to be installed or provided via `--exiftool-path`.

### `pillow`

Fallback mode for common formats. It should not be treated as full RAW support.

## Privacy model

The tool writes only relative paths to the output files. This avoids exposing full local paths such as user names, OneDrive paths, or internal folder names.

The `.gitignore` blocks local image data, generated output files, archives, and `TEMP/` folders.

## Output model

CSV and GeoJSON include only files with valid latitude and longitude.

The summary JSON contains scan counts, list of files without GPS metadata, and extraction errors.

## Testing strategy

Unit tests cover pure logic first, especially GPS coordinate conversion. Real image test files should not be committed unless they are synthetic, license-clean, and stripped of private metadata.
