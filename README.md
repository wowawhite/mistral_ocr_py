# Zeiterfassung OCR – handgeschriebene Zeitzettel zu Excel

Lokale (Offline-)Erkennung von Name, Datum, Arbeit-, Urlaubs- und
Krankheitstagen aus Fotos handgeschriebener Zeitzettel mit **Qwen3-VL-8B**
und Export als Excel-Datei. Es verlässt **keine Daten** den Rechner.

## Voraussetzungen

- Windows 10/11, NVIDIA RTX 3090 (Treiber aktuell)
- Python 3.11 oder 3.12 (64-bit)
- [Ollama für Windows](https://ollama.com/download) **≥ 0.12.7**

## Installation

```powershell
# 1. Modell laden (ca. 6.1 GB, einmalig)
ollama pull qwen3-vl:8b

# 2. Python-Abhängigkeiten
pip install -r requirements.txt

# Optional, für strikten Offline-Betrieb:
# Windows-Firewall -> ausgehende Regel für ollama.exe blockieren
```

## Nutzung

### GUI (empfohlen)

```powershell
run_app.bat
```

oder manuell: `python -m streamlit run app.py`

Ablauf in der GUI:
1. Ordner mit Fotos angeben und scannen
2. "Alle Fotos verarbeiten" – jede Seite erhält eine **Konfidenz 0-100 %**
   mit Ampelanzeige (grün ≥ 90 % / gelb ab 70 % / rot < 70 %)
3. Werte gegebenenfalls korrigieren ("Geprüft" markieren)
4. "Excel speichern" – schreibt lokal nach Dokumente\Zeiterfassung

### Kommandozeile (Batch)

```powershell
python cli.py <Ordner> -o Ergebnis.xlsx -v
```

Beide Wege erzeugen eine `.xlsx` mit den Spalten Name, Datum,
Arbeitstage, Urlaubstage, Krankheitstage, **Konfidenz (%)**,
Geprüft, Quelldatei sowie einem Statistikblatt.

## Konfidenz je Seite (0-100 %)

Zusammengesetzt aus vier Signalen:

| Signal | Gewicht |
|---|---|
| Modell-Selbsteinschätzung je Feld | 35 % |
| Konsistenz eines Zweitdurchlaufs (variiertes Sampling) | 30 % |
| Plausibilitätsregeln (Datums-/Tage-Summen, Format) | 20 % |
| Bildqualität (Schärfe, Kontrast, Helligkeit via OpenCV) | 15 % |

Ampel-Regel für den Umgang:
- **≥ 90 %** – Übernahme zulassen
- **70-89 %** – anzeigen und vom Nutzer bestätigen lassen
- **< 70 %** – manuelle Korrektur verpflichtend

## Projektstruktur

```
zeiterfassung/
├── app.py              # Streamlit-GUI
├── cli.py              # Kommandozeilen-Batchverarbeitung
├── pipeline.py         # Orchestrierung je Seite (inkl. Rot-Archiv)
├── ocr_engine.py       # Qwen3-VL-8B via Ollama (2 Durchläufe)
├── confidence.py       # Seiten-Konfidenz 0-100 %
├── validation.py       # Plausibilitätsprüfung
├── preprocessing.py    # Bildvorverarbeitung + Bildqualität (OpenCV)
├── excel_export.py     # Excel-Export mit Ampelformatierung
├── schemas.py          # Pydantic-Datenmodelle
├── config.py           # Modell, Schwellen, Gewichte, Pfade
├── requirements.txt
├── __main__.py         # python -m zeiterfassung
└── run_app.bat         # GUI-Start unter Windows
```

## Datenschutz

- Ollama lauscht standardmäßig nur auf `127.0.0.1` – nicht ändern
- Modell-Dateien liegen vollständig lokal
- Ausgabe-Excel nur auf der lokalen Platte
- Empfehlung: Windows-Firewall-Ausgangssperre für `ollama.exe`
