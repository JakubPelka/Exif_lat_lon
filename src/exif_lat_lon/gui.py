from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import scan_images, write_outputs

ROOT_DIR = Path.cwd()
DEFAULT_INPUT = ROOT_DIR / "indata" if (ROOT_DIR / "indata").exists() else ROOT_DIR
DEFAULT_OUTPUT = ROOT_DIR / "output" / "image_gps.csv"


class ExifLatLonApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Exif lat/lon → CSV + GeoJSON")
        self.root.geometry("860x430")
        self.root.minsize(760, 360)

        self.input_folder = tk.StringVar(value=str(DEFAULT_INPUT))
        self.output_file = tk.StringVar(value=str(DEFAULT_OUTPUT))
        self.extractor = tk.StringVar(value="auto")
        self.recursive = tk.BooleanVar(value=True)
        self._is_running = False
        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Folder z obrazami:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.input_folder).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 10))
        ttk.Button(frame, text="Wybierz folder", command=self.pick_folder).grid(row=1, column=1, sticky="ew", pady=(4, 10))

        ttk.Label(frame, text="Plik wynikowy CSV:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.output_file).grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(4, 10))
        ttk.Button(frame, text="Wybierz plik", command=self.pick_output).grid(row=3, column=1, sticky="ew", pady=(4, 10))

        options = ttk.Frame(frame)
        options.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        ttk.Label(options, text="Extractor:").pack(side="left")
        ttk.Combobox(options, textvariable=self.extractor, values=["auto", "exiftool", "pillow"], width=12, state="readonly").pack(side="left", padx=(6, 18))
        ttk.Checkbutton(options, text="Szukaj w podfolderach", variable=self.recursive).pack(side="left")

        info = (
            "Auto używa ExifTool, jeżeli jest dostępny w systemie. To najlepsza ścieżka dla RAW/HEIF/JPG. "
            "Jeżeli ExifTool nie jest dostępny, program używa fallbacku Pillow/pillow-heif."
        )
        ttk.Label(frame, text=info, wraplength=800, justify="left").grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.run_button = ttk.Button(frame, text="Uruchom eksport", command=self.run)
        self.run_button.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.status = tk.Text(frame, height=10, wrap="word")
        self.status.grid(row=7, column=0, columnspan=2, sticky="nsew")

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(7, weight=1)

    def pick_folder(self) -> None:
        folder = filedialog.askdirectory(title="Wybierz folder z obrazami", initialdir=self.input_folder.get())
        if folder:
            self.input_folder.set(folder)

    def pick_output(self) -> None:
        file_path = filedialog.asksaveasfilename(
            title="Wybierz plik CSV",
            initialdir=str(Path(self.output_file.get()).parent),
            initialfile=Path(self.output_file.get()).name,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Wszystkie pliki", "*.*")],
        )
        if file_path:
            self.output_file.set(file_path)

    def log(self, text: str) -> None:
        self.status.insert("end", text + "\n")
        self.status.see("end")

    def run(self) -> None:
        if self._is_running:
            return
        self.status.delete("1.0", "end")
        self._is_running = True
        self.run_button.configure(state="disabled")
        thread = threading.Thread(target=self._run_worker, daemon=True)
        thread.start()

    def _run_worker(self) -> None:
        try:
            self.root.after(0, lambda: self.log("Startuję skanowanie..."))
            result = scan_images(
                input_folder=self.input_folder.get(),
                recursive=self.recursive.get(),
                extractor=self.extractor.get(),
            )
            csv_path, geojson_path, summary_path, no_gps_path = write_outputs(result, self.output_file.get())
            lines = [
                f"Extractor: {result.extractor}",
                f"Przeskanowane obsługiwane pliki: {result.total_supported_files}",
                f"Pliki z GPS: {result.gps_count}",
                f"Pliki bez GPS: {result.no_gps_count}",
                f"Błędy: {result.error_count}",
                f"CSV: {csv_path}",
                f"GeoJSON: {geojson_path}",
                f"Raport: {summary_path}",
            ]
            if no_gps_path:
                lines.append(f"Lista plików bez GPS: {no_gps_path}")
            self.root.after(0, lambda: self._finish_success(lines))
        except Exception as exc:
            self.root.after(0, lambda: self._finish_error(str(exc)))

    def _finish_success(self, lines: list[str]) -> None:
        for line in lines:
            self.log(line)
        self._is_running = False
        self.run_button.configure(state="normal")
        messagebox.showinfo("Gotowe", "\n".join(lines))

    def _finish_error(self, message: str) -> None:
        self.log(f"ERROR: {message}")
        self._is_running = False
        self.run_button.configure(state="normal")
        messagebox.showerror("Błąd", message)


def main() -> None:
    root = tk.Tk()
    ExifLatLonApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
