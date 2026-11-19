@echo off
REM Startet die Zeiterfassungs-GUI (Streamlit) lokal ohne Cloud-Zugriff.
REM Voraussetzung: Ollama installiert, Modell geladen:
REM   ollama pull qwen3-vl:8b-instruct-q8_0
cd /d "%~dp0"
python -m streamlit run app.py
