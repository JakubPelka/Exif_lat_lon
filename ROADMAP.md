# Roadmap

## 0.1.x - cleanup and validation

- Validate the new structure on Windows.
- Test JPG/JPEG from phone and camera.
- Test HEIC/HEIF from iPhone.
- Test DNG from phone RAW workflow.
- Test selected camera RAW formats if available: CR3, NEF, ARW, RW2.
- Check whether ExifTool is available in the expected work environment.
- Confirm that CSV and GeoJSON open correctly in QGIS.

## 0.2.x - usability

- Add clearer GUI progress for large folders.
- Add export option: include files without GPS in CSV with empty coordinates.
- Add optional `datetime_original` normalization to ISO 8601.
- Add option to include relative folder fields separately.
- Add drag-and-drop support if a lightweight dependency is acceptable.

## 0.3.x - GIS workflow polish

- Add optional GeoPackage export.
- Add CRS metadata note in GeoJSON output documentation.
- Add QGIS usage guide with screenshots.
- Add release ZIP for non-technical users.

## Possible later ideas

- Duplicate detection by filename/date/coordinates.
- Reverse geocoding is intentionally not planned for now because it would require an external service and privacy decisions.
- Writing metadata back to images is intentionally out of scope for now.
