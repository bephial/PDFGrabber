#!/usr/bin/env python3
"""
pdf_downloader.py – Durchsucht eine Webseite nach PDF-Links und lädt sie herunter.

Installation:
    pip install requests beautifulsoup4

Beispiele:
    python pdf_downloader.py https://example.com/materialien
    python pdf_downloader.py https://example.com -o pdfs -t 2
    python pdf_downloader.py https://example.com --filter arbeitsblatt
"""

import argparse
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (PDF-Downloader)"}


def ist_pdf_link(url: str) -> bool:
    """Prüft anhand der URL, ob es sich (wahrscheinlich) um ein PDF handelt."""
    pfad = urlparse(url).path.lower()
    return pfad.endswith(".pdf")


def sicherer_dateiname(url: str, antwort: requests.Response | None = None) -> str:
    """Ermittelt einen sauberen Dateinamen aus Header oder URL."""
    if antwort is not None:
        cd = antwort.headers.get("Content-Disposition", "")
        treffer = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.I)
        if treffer:
            name = unquote(treffer.group(1))
            return re.sub(r'[\\/:*?"<>|]', "_", name)
    name = unquote(os.path.basename(urlparse(url).path)) or "dokument.pdf"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def eindeutiger_pfad(ordner: str, name: str) -> str:
    """Hängt _1, _2 … an, falls die Datei schon existiert."""
    basis, endung = os.path.splitext(name)
    pfad = os.path.join(ordner, name)
    i = 1
    while os.path.exists(pfad):
        pfad = os.path.join(ordner, f"{basis}_{i}{endung}")
        i += 1
    return pfad


def links_sammeln(session: requests.Session, url: str) -> tuple[set[str], set[str]]:
    """Gibt (pdf_links, seiten_links) einer HTML-Seite zurück."""
    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"  ! Seite nicht abrufbar: {url} ({e})")
        return set(), set()

    if "text/html" not in r.headers.get("Content-Type", ""):
        return set(), set()

    soup = BeautifulSoup(r.text, "html.parser")
    pdfs, seiten = set(), set()
    for tag in soup.find_all(["a", "iframe", "embed", "object"]):
        href = tag.get("href") or tag.get("src") or tag.get("data")
        if not href or href.startswith(("mailto:", "javascript:", "#")):
            continue
        absolut = urljoin(url, href).split("#")[0]
        if ist_pdf_link(absolut):
            pdfs.add(absolut)
        elif absolut.startswith(("http://", "https://")):
            seiten.add(absolut)
    return pdfs, seiten


def pdf_herunterladen(session: requests.Session, url: str, ordner: str) -> bool:
    try:
        with session.get(url, timeout=60, stream=True) as r:
            r.raise_for_status()
            typ = r.headers.get("Content-Type", "").lower()
            if "pdf" not in typ and "octet-stream" not in typ:
                print(f"  - übersprungen (kein PDF, {typ}): {url}")
                return False
            pfad = eindeutiger_pfad(ordner, sicherer_dateiname(url, r))
            with open(pfad, "wb") as f:
                for block in r.iter_content(chunk_size=65536):
                    f.write(block)
        print(f"  ✓ {os.path.basename(pfad)}")
        return True
    except requests.RequestException as e:
        print(f"  ✗ Fehler bei {url}: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description="PDFs von einer Webseite herunterladen.")
    p.add_argument("url", help="Start-URL der Webseite")
    p.add_argument("-o", "--ordner", default="pdf_downloads", help="Zielordner (Standard: pdf_downloads)")
    p.add_argument("-t", "--tiefe", type=int, default=0,
                   help="Wie viele Link-Ebenen weiter suchen (0 = nur diese Seite)")
    p.add_argument("--filter", help="Nur PDFs, deren URL diesen Text enthält (ohne Groß/Klein)")
    p.add_argument("--fremde-domains", action="store_true",
                   help="Beim Weitersuchen auch Seiten anderer Domains besuchen")
    p.add_argument("--pause", type=float, default=0.5, help="Pause zwischen Anfragen in Sekunden")
    p.add_argument("--nur-auflisten", action="store_true", help="PDFs nur anzeigen, nicht laden")
    args = p.parse_args()

    os.makedirs(args.ordner, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    start_domain = urlparse(args.url).netloc

    besucht: set[str] = set()
    alle_pdfs: set[str] = set()
    aktuelle_ebene = {args.url}

    for ebene in range(args.tiefe + 1):
        naechste_ebene: set[str] = set()
        for seite in aktuelle_ebene:
            if seite in besucht:
                continue
            besucht.add(seite)
            print(f"Durchsuche (Ebene {ebene}): {seite}")
            pdfs, seiten = links_sammeln(session, seite)
            alle_pdfs |= pdfs
            for s in seiten:
                if args.fremde_domains or urlparse(s).netloc == start_domain:
                    naechste_ebene.add(s)
            time.sleep(args.pause)
        aktuelle_ebene = naechste_ebene - besucht

    if args.filter:
        alle_pdfs = {u for u in alle_pdfs if args.filter.lower() in u.lower()}

    print(f"\n{len(alle_pdfs)} PDF(s) gefunden.")
    if not alle_pdfs:
        return
    if args.nur_auflisten:
        for u in sorted(alle_pdfs):
            print("  " + u)
        return

    erfolgreich = 0
    for u in sorted(alle_pdfs):
        if pdf_herunterladen(session, u, args.ordner):
            erfolgreich += 1
        time.sleep(args.pause)

    print(f"\nFertig: {erfolgreich}/{len(alle_pdfs)} gespeichert in '{os.path.abspath(args.ordner)}'.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nAbgebrochen.")
