#!/bin/sh
# Offline re-run (all pages cached under raw/). Set PG_OFFLINE=1 to forbid network. Without it, missing pages are fetched politely (>=2 s/host).
cd "$(dirname "$0")"
PY=../../../.venv/bin/python
PG_OFFLINE=${PG_OFFLINE:-1} python3 fetch_texts.py          # (cached) extracts text of each official box-score document
PG_OFFLINE=${PG_OFFLINE:-1} python3 build_games.py          # parse -> games_long.csv, games_qa.csv
$PY match_features.py                                       # pid match -> matches.csv, unmatched.csv, features.csv, coverage_*.csv
# OCR step (macOS Vision; only needed when raw/ocr is empty): ocr/ocr_pdf raw/pdf/<key>.pdf > raw/ocr/<key>.txt  (source ocr/ocr_pdf.swift)
