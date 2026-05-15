# Exif lat/lon

**Status:** EXPERIMENT / clean baseline 0.1.0

Small Python tool for extracting GPS coordinates from image metadata and exporting them to CSV and GeoJSON.

The project is designed for a simple workflow:

1. Put images in a local input folder.
2. Run the GUI or CLI.
3. Get GIS-friendly CSV and GeoJSON output.

The repository should contain code and documentation only. Do not commit private photos, RAW files, exported results, archives, local paths, API keys, or temporary working folders.

## What it supports

Best support is available when **ExifTool** is installed and available in your system `PATH`.

| Type | Extensions | Notes |
|---|---|---|
| Phone / standard images | `.jpg`, `.jpeg`, `.heic`, `.heif`, `.tif`, `.tiff`, `.webp` | Uses ExifTool when available. Falls back to Pillow/pillow-heif. |
| Camera RAW / phone RAW | `.dng`, `.cr2`, `.cr3`, `.nef`, `.arw`, `.rw2`, `.orf`, `.raf`, `.pef`, `.srw`, `.3fr`, `.erf`, `.kdc`, `.mrw`, `.nrw`, `.rwl`, `.iiq` | Requires ExifTool for reliable metadata extraction. |

Only files with embedded GPS metadata are exported as point features.

## Output files

If you choose:

```text
output/image_gps.csv
```

The tool creates:

```text
output/image_gps.csv
output/image_gps.geojson
output/image_gps_summary.json
output/image_gps_no_gps.txt   # only when files without GPS are found
```

### CSV columns

```text
filename,relative_path,extension,latitude,longitude,altitude_m,datetime_original,make,model,file_type,extractor
```

### GeoJSON

The GeoJSON output uses WGS84 coordinates:

```text
[longitude, latitude]
```

If altitude is available, coordinates are written as:

```text
[longitude, latitude, altitude_m]
```

## Installation

Recommended: Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
```

### Optional but recommended: ExifTool

ExifTool gives the best support for HEIF/HEIC and camera RAW formats.

After installation, check that it works:

```bash
exiftool -ver
```

If `exiftool` is not found, the tool still tries to use the Pillow fallback for common image formats, but RAW support will be limited.

## Run GUI

From the repository root:

```bash
python start.py
```

The GUI lets you choose:

- input folder
- output CSV file
- extractor mode: `auto`, `exiftool`, or `pillow`
- recursive scanning of subfolders

## Run CLI

Basic run:

```bash
python start.py --input indata --output output/image_gps.csv
```

Use ExifTool explicitly:

```bash
python start.py --input indata --output output/image_gps.csv --extractor exiftool
```

Use Pillow fallback explicitly:

```bash
python start.py --input indata --output output/image_gps.csv --extractor pillow
```

Scan only the selected folder, without subfolders:

```bash
python start.py --input indata --output output/image_gps.csv --no-recursive
```

## Repository structure

```text
.
├── start.py
├── src/
│   └── exif_lat_lon/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── core.py
│       └── gui.py
├── tests/
│   └── test_gps_conversion.py
├── docs/
│   └── architecture.md
├── sample_data/
│   └── README.md
├── .gitattributes
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── ROADMAP.md
├── pyproject.toml
└── requirements.txt
```

## Safety notes

This tool reads metadata from local files and writes new CSV/GeoJSON/report files. It does not upload images or metadata anywhere.

GPS metadata may reveal private locations. Be careful before sharing exported CSV/GeoJSON files publicly.

## Current limitations

- It extracts only existing embedded GPS metadata.
- It does not geocode files without GPS.
- RAW support depends on ExifTool being installed.
- The fallback Pillow path is useful for common formats, but it is not a full RAW metadata reader.
- Format support should be tested with real sample files from the target phone/camera workflow before a stable release.
