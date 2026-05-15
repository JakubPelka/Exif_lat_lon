from exif_lat_lon.core import dms_to_decimal, rational_to_float, resolve_output_paths


def test_rational_to_float_tuple():
    assert rational_to_float((3, 2)) == 1.5


def test_dms_to_decimal_north_east():
    assert round(dms_to_decimal(((56, 1), (7, 1), (30, 1)), "N"), 6) == 56.125
    assert round(dms_to_decimal(((12, 1), (30, 1), (0, 1)), "E"), 6) == 12.5


def test_dms_to_decimal_south_west():
    assert round(dms_to_decimal(((56, 1), (7, 1), (30, 1)), "S"), 6) == -56.125
    assert round(dms_to_decimal(((12, 1), (30, 1), (0, 1)), "W"), 6) == -12.5


def test_resolve_output_paths_from_csv():
    csv_path, geojson_path, summary_path, no_gps_path = resolve_output_paths("output/image_gps.csv")
    assert csv_path.as_posix() == "output/image_gps.csv"
    assert geojson_path.as_posix() == "output/image_gps.geojson"
    assert summary_path.as_posix() == "output/image_gps_summary.json"
    assert no_gps_path.as_posix() == "output/image_gps_no_gps.txt"
