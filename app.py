"""Streamlit-GUI: Ordner auswählen, verarbeiten, Konfidenz prüfen,
Werte korrigieren und Excel exportieren."""
import logging
from pathlib import Path

import streamlit as st

from config import (ARCHIVE_DIR_NAME, DEFAULT_OUTPUT, MODEL, THRESHOLD_GREEN,
                    THRESHOLD_YELLOW)
from excel_export import export, export_secondary_sheet
from pipeline import evaluation_to_row, list_images, process_image

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Zeiterfassung OCR", page_icon=":bar_chart:",
                   layout="wide")

st.title("Zeiterfassung aus Fotos (OCR, komplett lokal)")
st.caption(
    f"Modell: **{MODEL}** via Ollama auf 127.0.0.1 – "
    "kein Datentransfer in eine Cloud.")


# --- Sitzungszustand ------------------------------------------------------
for key in ("evaluations", "rows"):
    if key not in st.session_state:
        st.session_state[key] = []


def verdict_label(verdict: str) -> str:
    return {"GRUEN": "🟢 Hohe Konfidenz – automatische Übernahme",
            "GELB": "🟡 Mittlere Konfidenz – Werte bitte prüfen",
            "ROT": "🔴 Niedrige Konfidenz – manuelle Korrektur nötig"}[verdict]


# --- Eingabe -------------------------------------------------------------
st.subheader("1. Eingabeordner mit Fotos")
input_dir = st.text_input(
    "Ordnerpfad (z. B. C:\\Users\\<Name>\\Documents\\Zeitkarten)",
    value=str(Path.home() / "Documents" / "Zeitkarten"))

if st.button("Ordner scannen"):
    images = list_images(input_dir)
    if not images:
        st.error("Keine Bilder gefunden (JPG, PNG, BMP, WEBP, TIFF).")
    else:
        st.info(f"{len(images)} Bilder gefunden.")

st.subheader("2. Verarbeitung")
if st.button("Alle Fotos verarbeiten", type="primary"):
    images = list_images(input_dir)
    if not images:
        st.error("Keine Bilder im Ordner.")
    else:
        st.session_state.evaluations = []
        st.session_state.rows = []
        progress = st.progress(0.0, text="Verarbeitung läuft ...")
        for i, img in enumerate(images):
            try:
                ev = process_image(img)
            except Exception as exc:
                st.error(f"Fehler bei {img.name}: {exc}")
                continue
            st.session_state.evaluations.append(ev)
            st.session_state.rows.append(evaluation_to_row(ev))
            progress.progress(
                (i + 1) / len(images),
                text=f"{i + 1}/{len(images)}: {img.name} "
                     f"({ev.page_confidence} %)")
        progress.empty()

# --- Ergebnistabelle mit Konfidenz-Ampel ---------------------------------
if st.session_state.rows:
    st.subheader("3. Erkannte Werte und Konfidenz")
    st.write(f"Grün ab {THRESHOLD_GREEN} %: automatische Übernahme · "
             f"Gelb: {THRESHOLD_YELLOW}–{THRESHOLD_GREEN - 1} %: prüfen · "
             f"Rot: unter {THRESHOLD_YELLOW} %: korrigieren")

    edited_rows = []
    for idx, (row, ev) in enumerate(
            zip(st.session_state.rows, st.session_state.evaluations)):
        conf = int(row["confidence"])
        color = ("" if conf >= THRESHOLD_GREEN
                 else "🟡" if conf >= THRESHOLD_YELLOW else "🔴")
        with st.expander(f"{color} {row['quelle']} – Konfidenz {conf} %",
                         expanded=False):
            st.progress(conf / 100)
            with st.expander("Konfidenz-Aufschlüsselung", expanded=False):
                st.json(ev.quality_breakdown)
            if ev.issues:
                st.warning("Plausibilität: " + "; ".join(ev.issues))
            c = st.columns(6)
            row["name"] = c[0].text_input("Name", row["name"], key=f"n{idx}")
            row["datum"] = c[1].text_input("Datum", row["datum"],
                                           key=f"d{idx}")
            row["arbeitstage"] = c[2].number_input(
                "Arbeitstage", min_value=0, max_value=31, step=1,
                value=int(row["arbeitstage"] or 0), key=f"a{idx}")
            row["urlaubstage"] = c[3].number_input(
                "Urlaubstage", min_value=0, max_value=31, step=1,
                value=int(row["urlaubstage"] or 0), key=f"u{idx}")
            row["krankheitstage"] = c[4].number_input(
                "Krankheitstage", min_value=0, max_value=31, step=1,
                value=int(row["krankheitstage"] or 0), key=f"k{idx}")
            row["geprueft"] = c[5].checkbox("Geprüft", bool(row["geprueft"]),
                                            key=f"p{idx}")
            edited_rows.append(row)

    st.session_state.rows = edited_rows

    # --- Export ----------------------------------------------------------
    st.subheader("4. Excel-Export")
    out_name = st.text_input("Dateiname", "zeiterfassung.xlsx")
    if st.button("Excel speichern", type="primary"):
        out_path = Path.home() / "Documents" / "Zeiterfassung" / out_name
        written = export(st.session_state.rows, out_path.with_suffix(".xlsx"))
        export_secondary_sheet(st.session_state.rows, written)
        st.success(f"Gespeichert: {written}")
        n_rot = sum(1 for r in st.session_state.rows
                    if int(r["confidence"]) < THRESHOLD_YELLOW)
        if n_rot:
            st.info(f"{n_rot} Seiten unter {THRESHOLD_YELLOW} %: "
                    f"Fotos ggf. mit besserem Licht neu aufnehmen "
                    f"(siehe Ordner '{ARCHIVE_DIR_NAME}' im Eingabeordner).")
else:
    st.info("Noch keine Verarbeitung gestartet.")
