# HEIC EXIF till CSV och GeoJSON

Ett litet Python-verktyg med enkelt GUI som läser GPS-koordinater från **HEIC/HEIF-bilder** och exporterar resultatet till både **CSV** och **GeoJSON**.

Verktyget är gjort för ett enkelt arbetsflöde:

* välj en mapp med bilder
* välj namn och plats för utdatafilen
* kör
* få både `CSV` och `GeoJSON`

## Funktioner

* Läser **HEIC** och **HEIF**
* Söker i vald mapp och alla undermappar
* Hämtar GPS från bildens EXIF-data
* Sparar resultat som:

  * `filnamn.csv`
  * `filnamn.geojson`
* Enkelt gränssnitt med **tkinter**
* Svenska texter i dialogrutor och meddelanden
* Fil- och mappval startar som standard i den mapp där skriptet körs

## Utdata

### CSV

CSV-filen innehåller följande kolumner:

* `filename`
* `lat`
* `lon`

Exempel:

```csv
filename,lat,lon
IMG_1234.HEIC,56.123456,12.654321
IMG_1235.HEIC,56.123401,12.654399
```

### GeoJSON

GeoJSON-filen sparas automatiskt med samma filnamnsbas som CSV-filen.

Exempel:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "filename": "IMG_1234.HEIC"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [12.654321, 56.123456]
      }
    }
  ]
}
```

## Krav

* Python 3.10 eller senare rekommenderas
* Windows fungerar bra
* HEIC-stöd via `pillow-heif`

## Installation

Installera beroenden:

```bash
pip install pillow pillow-heif
```

## Körning

Starta skriptet:

```bash
python heic_exif_to_csv_geojson.py
```

## Så används verktyget

1. Starta skriptet.
2. Klicka på **Välj mapp** och välj mappen som innehåller dina HEIC-bilder.
3. Klicka på **Välj fil** och ange namn på utdatafilen för CSV.
4. Klicka på **Kör**.
5. Skriptet sparar:

   * en CSV-fil
   * en GeoJSON-fil

Om du till exempel väljer:

```text
C:\Data\bilder\resultat.csv
```

så skapas också automatiskt:

```text
C:\Data\bilder\resultat.geojson
```

## Hur GPS hämtas

Skriptet läser EXIF GPS-information från varje bild och omvandlar koordinater från:

* grader
* minuter
* sekunder

...till vanliga decimala koordinater (`lat`, `lon`).

Koordinater i sydlig eller västlig riktning får negativt värde enligt standard.

## Begränsningar

* Endast bilder med sparad GPS i EXIF kommer med i exporten.
* Bilder utan GPS ignoreras.
* Fokus ligger på **HEIC/HEIF**. Vill du även stödja JPG/JPEG kan skriptet utökas enkelt.

## Vanliga problem

### Inga bilder hittades

Kontrollera att:

* du valt rätt mapp
* bilderna verkligen är `.heic` eller `.heif`
* bilderna innehåller GPS-data

### Modulen `pillow_heif` saknas

Installera beroenden igen:

```bash
pip install pillow pillow-heif
```

### CSV skapas men inga rader finns

Det betyder oftast att bilderna saknar GPS i EXIF.

## Möjliga förbättringar

Vid behov kan verktyget senare byggas ut med till exempel:

* kolumn för full sökväg
* datum/tid från EXIF
* stöd för JPG/JPEG/TIFF
* drag-and-drop av mapp
* direkt export till punktlager för GIS-flöden

## Licens

Välj själv licens för projektet, till exempel MIT.
