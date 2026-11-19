"""Zentrale Konfiguration der Zeiterfassungs-Pipeline."""
from pathlib import Path

# --- Modell / Ollama -------------------------------------------------------
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen3-vl:8b-instruct-q8_0"
NUM_CTX = 8192

# Sampling für die beiden Durchläufe (Konsistenzprüfung)
TEMP_RUN1 = 0.0
TEMP_RUN2 = 0.7

# --- Confidence-Gewichtung ------------------------------------------------
W_MODEL_SELF = 0.35
W_CONSISTENCY = 0.30
W_PLAUSIBILITY = 0.20
W_IMAGE_QUALITY = 0.15

# --- Schwellenwerte -------------------------------------------------------
THRESHOLD_GREEN = 90   # ab hier automatische Übernahme
THRESHOLD_YELLOW = 70  # darunter manuelle Prüfung Pflicht

# --- Bildvorverarbeitung --------------------------------------------------
MAX_SIDE_PX = 1600     # längere Kante nach Skalierung
SHARPNESS_MIN = 100.0  # Laplace-Varianz, ab der Bildqualität = 1.0 gilt

# --- Pfade ----------------------------------------------------------------
DEFAULT_INPUT_DIR = Path.home() / "Documents" / "Zeitkarten"
DEFAULT_OUTPUT = Path.home() / "Documents" / "Zeiterfassung"
ARCHIVE_DIR_NAME = "archiv_erkannt"

# --- Excel ----------------------------------------------------------------
EXCEL_HEADERS = [
    "Name", "Datum", "Arbeitstage", "Urlaubstage",
    "Krankheitstage", "Konfidenz (%)", "Geprüft (Ja/Nein)",
]

SYSTEM_PROMPT = (
    "Du bist ein präziser OCR-Assistent für handschriftliche deutsche "
    "Zeitzettel. Extrahiere aus dem Foto folgende Merkmale:\n"
    "- name: Klartext des Namensfeldes\n"
    "- datum: Format TT.MM.JJJJ\n"
    "- arbeitstage: Anzahl der gearbeiteten Tage (ganzahlige Zahl)\n"
    "- urlaubstage: Anzahl der Urlaubstage (ganzahlige Zahl)\n"
    "- krankheitstage: Anzahl der Krankheitstage (ganzahlige Zahl)\n"
    "\n"
    "Antworte AUSSCHLIESSLICH mit einem JSON-Objekt in genau diesem Format:\n"
    '{"name": {"value": "<Name>", "confidence": <0-100>}, '
    '"datum": {"value": "<TT.MM.JJJJ>", "confidence": <0-100>}, '
    '"arbeitstage": <Zahl>, "urlaubstage": <Zahl>, '
    '"krankheitstage": <Zahl>, '
    '"arbeitstage_conf": <0-100>, "urlaubstage_conf": <0-100>, '
    '"krankheitstage_conf": <0-100>}\n'
    "\n"
    "Kein zusätzlicher Text, keine Erklärung. Thinking nicht ausgeben. "
    "Bei nicht lesbaren Feldern: value = \"\" und confidence = 0."
)
