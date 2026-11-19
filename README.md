# Zeiterfassung OCR – lokale Handschriftenerkennung

Lokale Verarbeitung von Fotos handschriftlicher Zeitzettel mit Qwen3-VL-8B über Ollama. Die Anwendung exportiert erkannte Felder und Verarbeitungsstatus nach Excel.

## Voraussetzungen

- Windows 10/11 oder Linux/macOS
- Python 3.11 oder 3.12
- Ollama (lokal erreichbar)
- Modell `qwen3-vl:8b-instruct-q8_0`

```powershell
ollama pull qwen3-vl:8b-instruct-q8_0
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Start

GUI:

```powershell
python -m streamlit run app.py
```

CLI:

```powershell
python cli.py C:\\Pfad\\Zu\\Zeitkarten -o Ergebnis.xlsx -v
```

## Konfiguration

Optionale Umgebungsvariablen:

| Variable | Default | Zweck |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Lokaler Ollama-Endpunkt |
| `OCR_MODEL` | `qwen3-vl:8b-instruct-q8_0` | Modell-Tag |
| `OCR_NUM_CTX` | `8192` | Kontextfenster |
| `OLLAMA_TIMEOUT` | `180` | Timeout in Sekunden |
| `OCR_RETRIES` | `1` | Zusätzliche Versuche pro OCR-Aufruf |

## Qualitätswert und menschliche Prüfung

Der Qualitätswert 0–100 ist eine **heuristische Kennzahl**, keine kalibrierte Wahrscheinlichkeit. Er kombiniert Modellselbsteinschätzung, Konsistenz zweier OCR-Durchläufe, Plausibilität und Bildqualität. Er muss mit einem manuell annotierten Datensatz validiert werden, bevor er für automatische Entscheidungen eingesetzt wird.

Ein hoher Qualitätswert bedeutet nicht, dass ein Mensch das Dokument geprüft hat. Das Feld `Geprüft` wird daher ausschließlich durch explizite Benutzerbestätigung gesetzt.

## Fehler- und Exportverhalten

- Jedes Eingabebild erhält einen Ergebnisdatensatz – auch bei OCR-/Bildfehlern.
- Fehlerhafte Dokumente werden mit Status `failed`, Qualitätswert 0 und Fehlertext exportiert.
- Quelldateien werden standardmäßig nicht verschoben oder gelöscht.
- OCR-Strings, die wie Excel-Formeln beginnen, werden als Text escaped.
- Das Workbook enthält ein Blatt `Zeiterfassung` und ein Blatt `Statistik`.
- GUI und CLI verwenden dieselbe Batch-Service-Funktion.

## Tests

```powershell
pytest -q
```

Die Tests benötigen keine laufende Ollama-Instanz.

## Projektstruktur

```text
app.py                 Streamlit GUI
cli.py                 CLI
pipeline.py            Gemeinsame Batch-Verarbeitung
ocr_engine.py          Ollama / Qwen OCR
preprocessing.py       OpenCV Bildvorverarbeitung
confidence.py          Heuristischer Qualitätswert
validation.py           Feld- und Plausibilitätsprüfung
schemas.py              Pydantic Datenmodelle
excel_export.py         Excel-Export und Statistik
config.py               Umgebungsbasierte Konfiguration
tests/                  Automatisierte Tests
```

## Datenschutz und Betrieb

Die Anwendung ist für lokale Ollama-Verarbeitung ausgelegt. `OLLAMA_HOST` sollte auf Loopback (`127.0.0.1`) zeigen, wenn kein Zugriff aus dem Netzwerk beabsichtigt ist. Beachten Sie, dass lokale Verarbeitung allein keine vollständige Datenschutz- oder Sicherheitsprüfung ersetzt.
