from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Literal

try:
    from PIL import ExifTags, Image
except Exception:  # pragma: no cover - handled at runtime
    ExifTags = None
    Image = None

try:
    from pillow_heif import register_heif_opener
except Exception:  # pragma: no cover - optional HEIF support
    register_heif_opener = None

ExtractorMode = Literal["auto", "exiftool", "pillow"]

RASTER_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".heic", ".heif", ".tif", ".tiff", ".webp",
}

RAW_EXTENSIONS = {
    ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".srf", ".sr2",
    ".rw2", ".orf", ".raf", ".pef", ".ptx", ".srw", ".3fr", ".erf",
    ".kdc", ".dcr", ".mef", ".mos", ".mrw", ".rwl", ".iiq",
}

SUPPORTED_EXTENSIONS = RASTER_EXTENSIONS | RAW_EXTENSIONS
CSV_COLUMNS = [
    "filename",
    "relative_path",
    "extension",
    "latitude",
    "longitude",
    "altitude_m",
    "datetime_original",
    "make",
    "model",
    "file_type",
    "extractor",
]

GPS_IFD_TAG = 34853
GPS_LATITUDE_TAG = 2
GPS_LATITUDE_REF_TAG = 1
GPS_LONGITUDE_TAG = 4
GPS_LONGITUDE_REF_TAG = 3
GPS_ALTITUDE_TAG = 6
GPS_ALTITUDE_REF_TAG = 5
EXIF_DATETIME_ORIGINAL_TAG = 36867
EXIF_CREATE_DATE_TAG = 36868
EXIF_MAKE_TAG = 271
EXIF_MODEL_TAG = 272


@dataclass(slots=True)
class ImageGpsRecord:
    filename: str
    relative_path: str
    extension: str
    latitude: float
    longitude: float
    altitude_m: float | None = None
    datetime_original: str | None = None
    make: str | None = None
    model: str | None = None
    file_type: str | None = None
    extractor: str = "unknown"


@dataclass(slots=True)
class ScanError:
    relative_path: str
    message: str


@dataclass(slots=True)
class ScanResult:
    input_folder: str
    extractor: str
    total_supported_files: int
    gps_records: list[ImageGpsRecord]
    files_without_gps: list[str]
    errors: list[ScanError]

    @property
    def gps_count(self) -> int:
        return len(self.gps_records)

    @property
    def no_gps_count(self) -> int:
        return len(self.files_without_gps)

    @property
    def error_count(self) -> int:
        return len(self.errors)


def ensure_heif_registered() -> None:
    if register_heif_opener is not None:
        register_heif_opener()


def exiftool_available(exiftool_path: str | None = None) -> bool:
    executable = exiftool_path or "exiftool"
    return shutil.which(executable) is not None or Path(executable).exists()


def iter_supported_files(input_folder: Path, recursive: bool = True) -> list[Path]:
    pattern_iter: Iterable[Path]
    pattern_iter = input_folder.rglob("*") if recursive else input_folder.glob("*")
    files = [p for p in pattern_iter if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files, key=lambda p: str(p).lower())


def rational_to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        pass
    try:
        return float(value[0]) / float(value[1])
    except Exception:
        pass
    try:
        numerator = getattr(value, "numerator")
        denominator = getattr(value, "denominator")
        return float(numerator) / float(denominator)
    except Exception:
        return None


def dms_to_decimal(dms: Any, ref: Any) -> float | None:
    if dms is None or ref is None:
        return None
    try:
        if len(dms) != 3:
            return None
    except Exception:
        return None

    degrees = rational_to_float(dms[0])
    minutes = rational_to_float(dms[1])
    seconds = rational_to_float(dms[2])
    if degrees is None or minutes is None or seconds is None:
        return None

    decimal = degrees + minutes / 60.0 + seconds / 3600.0
    ref_text = str(ref).strip().upper()
    if ref_text in {"S", "W", "B'S'", "B'W'"}:
        decimal = -decimal
    return decimal


def _path_relative_to(file_path: Path, input_folder: Path) -> str:
    try:
        return file_path.relative_to(input_folder).as_posix()
    except ValueError:
        return file_path.name


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _pillow_gps_ifd(exif: Any) -> dict[Any, Any] | None:
    if not exif:
        return None
    try:
        gps_ifd = exif.get_ifd(GPS_IFD_TAG)
        if gps_ifd:
            return dict(gps_ifd)
    except Exception:
        pass
    try:
        gps_ifd = exif.get(GPS_IFD_TAG)
        if isinstance(gps_ifd, dict):
            return gps_ifd
    except Exception:
        pass
    return None


def extract_gps_with_pillow(file_path: Path, input_folder: Path) -> tuple[ImageGpsRecord | None, str | None]:
    if Image is None:
        return None, "Pillow is not installed. Install dependencies from requirements.txt."

    ensure_heif_registered()
    try:
        with Image.open(file_path) as image:
            exif = image.getexif()
            gps_ifd = _pillow_gps_ifd(exif)
            if not gps_ifd:
                return None, None

            latitude = dms_to_decimal(gps_ifd.get(GPS_LATITUDE_TAG), gps_ifd.get(GPS_LATITUDE_REF_TAG))
            longitude = dms_to_decimal(gps_ifd.get(GPS_LONGITUDE_TAG), gps_ifd.get(GPS_LONGITUDE_REF_TAG))
            if latitude is None or longitude is None:
                return None, None

            altitude = rational_to_float(gps_ifd.get(GPS_ALTITUDE_TAG))
            altitude_ref = gps_ifd.get(GPS_ALTITUDE_REF_TAG)
            if altitude is not None and altitude_ref in (1, b"\x01", "1"):
                altitude = -altitude

            datetime_original = _clean_text(exif.get(EXIF_DATETIME_ORIGINAL_TAG) or exif.get(EXIF_CREATE_DATE_TAG))
            make = _clean_text(exif.get(EXIF_MAKE_TAG))
            model = _clean_text(exif.get(EXIF_MODEL_TAG))

            return ImageGpsRecord(
                filename=file_path.name,
                relative_path=_path_relative_to(file_path, input_folder),
                extension=file_path.suffix.lower(),
                latitude=latitude,
                longitude=longitude,
                altitude_m=altitude,
                datetime_original=datetime_original,
                make=make,
                model=model,
                file_type=file_path.suffix.lower().lstrip(".").upper(),
                extractor="pillow",
            ), None
    except Exception as exc:
        return None, str(exc)


def _chunked(items: list[Path], size: int) -> Iterable[list[Path]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _exiftool_datetime(entry: dict[str, Any]) -> str | None:
    for key in ("SubSecDateTimeOriginal", "DateTimeOriginal", "CreateDate", "MediaCreateDate"):
        value = _clean_text(entry.get(key))
        if value:
            return value
    return None


def _record_from_exiftool_entry(entry: dict[str, Any], input_folder: Path) -> tuple[ImageGpsRecord | None, str | None]:
    source = entry.get("SourceFile")
    if not source:
        return None, "ExifTool returned metadata without SourceFile."

    file_path = Path(source)
    latitude = _clean_float(entry.get("GPSLatitude"))
    longitude = _clean_float(entry.get("GPSLongitude"))
    if latitude is None or longitude is None:
        return None, None

    return ImageGpsRecord(
        filename=file_path.name,
        relative_path=_path_relative_to(file_path, input_folder),
        extension=file_path.suffix.lower(),
        latitude=latitude,
        longitude=longitude,
        altitude_m=_clean_float(entry.get("GPSAltitude")),
        datetime_original=_exiftool_datetime(entry),
        make=_clean_text(entry.get("Make")),
        model=_clean_text(entry.get("Model")),
        file_type=_clean_text(entry.get("FileType")),
        extractor="exiftool",
    ), None


def extract_gps_with_exiftool(files: list[Path], input_folder: Path, exiftool_path: str | None = None) -> tuple[list[ImageGpsRecord], list[str], list[ScanError]]:
    executable = exiftool_path or "exiftool"
    records: list[ImageGpsRecord] = []
    files_without_gps: list[str] = []
    errors: list[ScanError] = []
    seen: set[str] = set()

    for batch in _chunked(files, 100):
        command = [
            executable,
            "-j",
            "-n",
            "-GPSLatitude",
            "-GPSLongitude",
            "-GPSAltitude",
            "-DateTimeOriginal",
            "-SubSecDateTimeOriginal",
            "-CreateDate",
            "-MediaCreateDate",
            "-Make",
            "-Model",
            "-FileType",
            *[str(path) for path in batch],
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except Exception as exc:
            for path in batch:
                errors.append(ScanError(_path_relative_to(path, input_folder), str(exc)))
            continue

        if not completed.stdout.strip():
            message = completed.stderr.strip() or f"ExifTool returned exit code {completed.returncode}."
            for path in batch:
                errors.append(ScanError(_path_relative_to(path, input_folder), message))
            continue

        try:
            metadata_entries = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            for path in batch:
                errors.append(ScanError(_path_relative_to(path, input_folder), f"Could not parse ExifTool JSON: {exc}"))
            continue

        for entry in metadata_entries:
            source = entry.get("SourceFile")
            if source:
                seen.add(str(Path(source).resolve()))
            record, message = _record_from_exiftool_entry(entry, input_folder)
            if record:
                records.append(record)
            elif message:
                rel = _path_relative_to(Path(source), input_folder) if source else "unknown"
                errors.append(ScanError(rel, message))
            elif source:
                files_without_gps.append(_path_relative_to(Path(source), input_folder))

    for path in files:
        if str(path.resolve()) not in seen:
            errors.append(ScanError(_path_relative_to(path, input_folder), "ExifTool returned no metadata for this file."))

    return records, sorted(files_without_gps), errors


def scan_images(
    input_folder: str | Path,
    recursive: bool = True,
    extractor: ExtractorMode = "auto",
    exiftool_path: str | None = None,
) -> ScanResult:
    folder = Path(input_folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Input folder does not exist or is not a folder: {folder}")

    files = iter_supported_files(folder, recursive=recursive)
    selected_extractor: str

    if extractor == "auto":
        selected_extractor = "exiftool" if exiftool_available(exiftool_path) else "pillow"
    else:
        selected_extractor = extractor

    if selected_extractor == "exiftool":
        if not exiftool_available(exiftool_path):
            raise RuntimeError("ExifTool was selected but was not found. Install ExifTool or use --extractor pillow.")
        gps_records, files_without_gps, errors = extract_gps_with_exiftool(files, folder, exiftool_path=exiftool_path)
    elif selected_extractor == "pillow":
        gps_records = []
        files_without_gps = []
        errors = []
        for file_path in files:
            record, message = extract_gps_with_pillow(file_path, folder)
            if record:
                gps_records.append(record)
            elif message:
                errors.append(ScanError(_path_relative_to(file_path, folder), message))
            else:
                files_without_gps.append(_path_relative_to(file_path, folder))
    else:
        raise ValueError(f"Unknown extractor mode: {extractor}")

    gps_records.sort(key=lambda record: record.relative_path.lower())
    return ScanResult(
        input_folder=str(folder),
        extractor=selected_extractor,
        total_supported_files=len(files),
        gps_records=gps_records,
        files_without_gps=sorted(files_without_gps),
        errors=errors,
    )


def resolve_output_paths(output_path: str | Path) -> tuple[Path, Path, Path, Path]:
    path = Path(output_path).expanduser()
    if path.suffix.lower() == ".csv":
        csv_path = path
        base = path.with_suffix("")
    elif path.suffix:
        base = path.with_suffix("")
        csv_path = base.with_suffix(".csv")
    else:
        base = path
        csv_path = path.with_suffix(".csv")

    geojson_path = base.with_suffix(".geojson")
    summary_path = Path(f"{base}_summary.json")
    no_gps_path = Path(f"{base}_no_gps.txt")
    return csv_path, geojson_path, summary_path, no_gps_path


def write_csv(records: list[ImageGpsRecord], csv_path: str | Path) -> None:
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_geojson(records: list[ImageGpsRecord], geojson_path: str | Path) -> None:
    path = Path(geojson_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    features: list[dict[str, Any]] = []
    for record in records:
        coordinates: list[float] = [record.longitude, record.latitude]
        if record.altitude_m is not None:
            coordinates.append(record.altitude_m)
        properties = asdict(record)
        properties.pop("latitude", None)
        properties.pop("longitude", None)
        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": {
                "type": "Point",
                "coordinates": coordinates,
            },
        })

    geojson = {
        "type": "FeatureCollection",
        "name": path.stem,
        "features": features,
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(geojson, file, ensure_ascii=False, indent=2)


def write_summary(result: ScanResult, summary_path: str | Path) -> None:
    path = Path(summary_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "input_folder": result.input_folder,
        "extractor": result.extractor,
        "total_supported_files": result.total_supported_files,
        "gps_count": result.gps_count,
        "no_gps_count": result.no_gps_count,
        "error_count": result.error_count,
        "files_without_gps": result.files_without_gps,
        "errors": [asdict(error) for error in result.errors],
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
    }
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def write_no_gps_list(result: ScanResult, no_gps_path: str | Path) -> None:
    if not result.files_without_gps:
        return
    path = Path(no_gps_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(result.files_without_gps) + "\n", encoding="utf-8")


def write_outputs(result: ScanResult, output_path: str | Path) -> tuple[Path, Path, Path, Path | None]:
    csv_path, geojson_path, summary_path, no_gps_path = resolve_output_paths(output_path)
    write_csv(result.gps_records, csv_path)
    write_geojson(result.gps_records, geojson_path)
    write_summary(result, summary_path)
    written_no_gps_path: Path | None = None
    if result.files_without_gps:
        write_no_gps_list(result, no_gps_path)
        written_no_gps_path = no_gps_path
    return csv_path, geojson_path, summary_path, written_no_gps_path
