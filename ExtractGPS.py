import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ExifTags
from pillow_heif import register_heif_opener


register_heif_opener()

SUPPORTED_EXTENSIONS = {".heic", ".heif"}
START_DIR = Path.cwd()


def rational_to_float(value):
    try:
        return float(value)
    except Exception:
        try:
            return value[0] / value[1]
        except Exception:
            return None


def dms_to_decimal(dms, ref):
    if not dms or not ref or len(dms) != 3:
        return None

    deg = rational_to_float(dms[0])
    minute = rational_to_float(dms[1])
    sec = rational_to_float(dms[2])

    if deg is None or minute is None or sec is None:
        return None

    dec = deg + minute / 60.0 + sec / 3600.0

    ref_str = str(ref)
    if ref_str.upper() in ("S", "W"):
        dec = -dec

    return dec


def extract_gps(image_path):
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if not exif:
                return None, None

            gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
            if not gps_ifd:
                return None, None

            lat = gps_ifd.get(ExifTags.GPS.GPSLatitude)
            lat_ref = gps_ifd.get(ExifTags.GPS.GPSLatitudeRef)
            lon = gps_ifd.get(ExifTags.GPS.GPSLongitude)
            lon_ref = gps_ifd.get(ExifTags.GPS.GPSLongitudeRef)

            lat_dd = dms_to_decimal(lat, lat_ref)
            lon_dd = dms_to_decimal(lon, lon_ref)

            return lat_dd, lon_dd
    except Exception:
        return None, None


def scan_folder(folder_path):
    rows = []

    for file_path in Path(folder_path).rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            lat, lon = extract_gps(file_path)
            if lat is not None and lon is not None:
                rows.append({
                    "filename": file_path.name,
                    "lat": lat,
                    "lon": lon
                })

    rows.sort(key=lambda x: x["filename"].lower())
    return rows


def write_csv(rows, csv_path):
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)


def write_geojson(rows, geojson_path):
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    for row in rows:
        geojson["features"].append({
            "type": "Feature",
            "properties": {
                "filename": row["filename"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]]
            }
        })

    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("HEIC EXIF till CSV och GeoJSON")
        self.root.geometry("780x300")
        self.root.minsize(720, 260)

        self.input_folder = tk.StringVar(value=str(START_DIR))
        self.output_csv = tk.StringVar(value=str(START_DIR / "heic_gps.csv"))

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Mapp med bilder:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(main, textvariable=self.input_folder, width=78).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(main, text="Välj mapp", command=self.pick_folder).grid(row=1, column=1, sticky="ew")

        ttk.Label(main, text="Utdatafil (CSV):").grid(row=2, column=0, sticky="w", pady=(14, 6))
        ttk.Entry(main, textvariable=self.output_csv, width=78).grid(row=3, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(main, text="Välj fil", command=self.pick_output).grid(row=3, column=1, sticky="ew")

        info_text = (
            "Skriptet söker efter HEIC/HEIF-bilder i vald mapp och undermappar.\n"
            "Det sparar både CSV och GeoJSON med samma filnamnsbas."
        )
        ttk.Label(main, text=info_text, justify="left").grid(row=4, column=0, columnspan=2, sticky="w", pady=(14, 10))

        ttk.Button(main, text="Kör", command=self.run).grid(row=5, column=0, columnspan=2, sticky="ew")

        self.status = tk.Text(main, height=7, wrap="word")
        self.status.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(14, 0))

        main.columnconfigure(0, weight=1)
        main.rowconfigure(6, weight=1)

    def log(self, text):
        self.status.insert("end", text + "\n")
        self.status.see("end")
        self.root.update_idletasks()

    def pick_folder(self):
        folder = filedialog.askdirectory(
            title="Välj mapp med HEIC-bilder",
            initialdir=str(START_DIR)
        )
        if folder:
            self.input_folder.set(folder)

    def pick_output(self):
        file_path = filedialog.asksaveasfilename(
            title="Välj namn på CSV-fil",
            initialdir=str(START_DIR),
            initialfile="heic_gps.csv",
            defaultextension=".csv",
            filetypes=[("CSV-filer", "*.csv")]
        )
        if file_path:
            self.output_csv.set(file_path)

    def run(self):
        folder = self.input_folder.get().strip()
        csv_path = self.output_csv.get().strip()

        self.status.delete("1.0", "end")

        if not folder:
            messagebox.showerror("Fel", "Välj en mapp med bilder.")
            return

        if not csv_path:
            messagebox.showerror("Fel", "Välj en utdatafil för CSV.")
            return

        folder_path = Path(folder)
        csv_file = Path(csv_path)

        if not folder_path.exists() or not folder_path.is_dir():
            messagebox.showerror("Fel", "Den valda mappen finns inte.")
            return

        if csv_file.suffix.lower() != ".csv":
            csv_file = csv_file.with_suffix(".csv")
            self.output_csv.set(str(csv_file))

        geojson_file = csv_file.with_suffix(".geojson")

        self.log(f"Läser mapp: {folder_path}")
        rows = scan_folder(folder_path)
        self.log(f"Antal bilder med GPS hittade: {len(rows)}")

        if not rows:
            messagebox.showwarning("Ingen data", "Inga HEIC-bilder med GPS-data hittades.")
            return

        write_csv(rows, csv_file)
        self.log(f"CSV sparad: {csv_file}")

        write_geojson(rows, geojson_file)
        self.log(f"GeoJSON sparad: {geojson_file}")

        messagebox.showinfo(
            "Klart",
            f"Filer sparade:\n{csv_file}\n{geojson_file}\n\nAntal poster: {len(rows)}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()