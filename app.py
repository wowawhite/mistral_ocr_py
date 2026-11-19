"""Streamlit interface for local OCR processing and human review."""
import logging
from pathlib import Path
import streamlit as st

from config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT, MODEL, THRESHOLD_GREEN, THRESHOLD_YELLOW
from excel_export import export
from pipeline import evaluation_to_row, list_images, process_batch
from schemas import FieldResult, PageResult
from validation import check_plausibility

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="Zeiterfassung OCR", page_icon="📊", layout="wide")
st.title("Zeiterfassung aus Fotos")
st.caption(f"Lokale Verarbeitung mit {MODEL} via Ollama. Keine Cloud-OCR.")

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "rows" not in st.session_state:
    st.session_state.rows = []

input_dir = st.text_input("Eingabeordner", str(DEFAULT_INPUT_DIR))
images = list_images(input_dir)
st.caption(f"{len(images)} unterstützte Bilddatei(en) gefunden.")
if st.button("Alle Fotos verarbeiten", type="primary", disabled=not images):
    bar = st.progress(0, text="Verarbeitung läuft …")
    try:
        bar.progress(0.15, text="OCR-Batch wird gestartet …")
        st.session_state.evaluations = process_batch(input_dir)
        st.session_state.rows = [evaluation_to_row(ev) for ev in st.session_state.evaluations]
        st.success(f"{len(st.session_state.rows)} Dokumente verarbeitet (einschließlich Fehlerdatensätzen).")
    except Exception as exc:
        st.error(str(exc))
    bar.empty()

if st.session_state.rows:
    rows = st.session_state.rows
    total = len(rows)
    failed = sum(row["status"] != "processed" for row in rows)
    reviewed = sum(bool(row["geprueft"]) for row in rows)
    a, b, c = st.columns(3)
    a.metric("Dokumente", total)
    b.metric("Fehlgeschlagen", failed)
    c.metric("Menschlich geprüft", reviewed)

    for idx, row in enumerate(rows):
        ev = st.session_state.evaluations[idx]
        with st.expander(f"{row['quelle']} · {row['confidence']}% · {row['status']}", expanded=ev.status != "processed"):
            if ev.error:
                st.error(ev.error)
            if ev.issues:
                st.warning(" / ".join(ev.issues))
            st.caption("Qualitätswert ist eine Heuristik, keine statistische Fehlerwahrscheinlichkeit.")
            cols = st.columns(5)
            row["name"] = cols[0].text_input("Name", row["name"], key=f"name_{idx}")
            row["datum"] = cols[1].text_input("Datum", row["datum"], key=f"date_{idx}")
            row["arbeitstage"] = cols[2].number_input("Arbeitstage", 0, 31, int(row["arbeitstage"]), key=f"work_{idx}")
            row["urlaubstage"] = cols[3].number_input("Urlaubstage", 0, 31, int(row["urlaubstage"]), key=f"leave_{idx}")
            row["krankheitstage"] = cols[4].number_input("Krankheitstage", 0, 31, int(row["krankheitstage"]), key=f"sick_{idx}")
            row["geprueft"] = "Ja" if st.checkbox("Von Mensch geprüft", value=bool(row["geprueft"]), key=f"review_{idx}") else ""
            corrected = PageResult(
                name=FieldResult(value=row["name"], confidence=100 if row["geprueft"] else ev.result.name.confidence),
                datum=FieldResult(value=row["datum"], confidence=100 if row["geprueft"] else ev.result.datum.confidence),
                arbeitstage=row["arbeitstage"], urlaubstage=row["urlaubstage"],
                krankheitstage=row["krankheitstage"],
            )
            _, validation_issues = check_plausibility(corrected)
            if validation_issues:
                st.error("Validierungsfehler: " + "; ".join(validation_issues))
            elif row["geprueft"]:
                st.success("Menschliche Prüfung dokumentiert.")
    st.session_state.rows = rows

    st.subheader("Excel-Export")
    output_name = st.text_input("Ausgabedatei", "zeiterfassung.xlsx")
    invalid_reviewed = []
    for row in rows:
        if row["geprueft"]:
            corrected = PageResult(
                name=FieldResult(value=row["name"], confidence=100),
                datum=FieldResult(value=row["datum"], confidence=100),
                arbeitstage=row["arbeitstage"], urlaubstage=row["urlaubstage"],
                krankheitstage=row["krankheitstage"])
            valid, problems = check_plausibility(corrected)
            if not valid:
                invalid_reviewed.append((row["quelle"], problems))
    if invalid_reviewed:
        st.error("Export gesperrt: als geprüft markierte Datensätze enthalten Validierungsfehler.")
    if st.button("Excel speichern", type="primary", disabled=bool(invalid_reviewed)):
        output = DEFAULT_OUTPUT / Path(output_name).name
        written = export(rows, output.with_suffix(".xlsx"))
        st.success(f"Gespeichert: {written}")
        st.info("Nicht geprüfte und fehlgeschlagene Einträge bleiben im Export sichtbar.")
else:
    st.info("Bitte einen Eingabeordner auswählen und die Verarbeitung starten.")
