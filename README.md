# PDF-Downloader

Ein kleines Python-Skript, das eine Webseite nach PDF-Dateien durchsucht und sie herunterlädt. Auf Wunsch folgt es auch Links auf Unterseiten.

## Voraussetzungen

- Python 3.10 oder neuer
- Die Pakete `requests` und `beautifulsoup4`:

```bash
pip install requests beautifulsoup4
```

## Verwendung

```bash
python pdfgrabber.py <URL> [Optionen]
```

Ohne Optionen lädt das Skript alle PDFs, die direkt auf der angegebenen Seite verlinkt sind, in den Ordner `pdf_downloads/`.

### Optionen

| Option | Bedeutung |
|---|---|
| `-o`, `--ordner NAME` | Zielordner (Standard: `pdf_downloads`) |
| `-t`, `--tiefe N` | Wie viele Link-Ebenen weiter gesucht wird (Standard: `0` = nur die Startseite) |
| `--filter TEXT` | Nur PDFs laden, deren URL diesen Text enthält (Groß-/Kleinschreibung egal) |
| `--fremde-domains` | Beim Weitersuchen auch Seiten anderer Domains besuchen |
| `--pause SEK` | Pause zwischen den Anfragen in Sekunden (Standard: `0.5`) |
| `--nur-auflisten` | Gefundene PDFs nur anzeigen, nicht herunterladen |

### Beispiele

```bash
# Alle PDFs einer Seite herunterladen
python pdfgrabber.py https://example.com/materialien

# Eine Ebene tiefer suchen und in den Ordner "skripte" speichern
python pdfgrabber.py https://example.com -t 1 -o skripte

# Nur Arbeitsblätter, vorher anzeigen lassen
python pdfgrabber.py https://example.com --filter arbeitsblatt --nur-auflisten
```

## So funktioniert's

1. Die Startseite wird abgerufen und nach Links durchsucht (`<a>`, `<iframe>`, `<embed>`, `<object>`).
2. Links, die auf `.pdf` enden, werden gesammelt. Bei `--tiefe` größer als 0 werden die übrigen Links als nächste Ebene besucht, standardmäßig nur auf derselben Domain.
3. Jede gefundene Datei wird heruntergeladen, sofern der Server sie wirklich als PDF ausliefert.
4. Der Dateiname kommt aus dem Server-Header oder aus der URL. Wenn es den Namen schon gibt, wird `_1`, `_2` usw. angehängt, sodass nichts überschrieben wird.

## Grenzen

- **JavaScript-Seiten:** Wenn eine Seite ihre Links erst per JavaScript nachlädt, findet das Skript sie nicht.
- **Login:** Seiten hinter einer Anmeldung (z. B. Moodle) werden nicht unterstützt.
- **PDF-Links ohne `.pdf`-Endung** (z. B. `download.php?id=12`) werden nicht erkannt.

## Hinweis

Bitte nur Dateien herunterladen, die du auch nutzen darfst, und die Nutzungsbedingungen der Webseite beachten. Bei vielen Ebenen (`-t 2` oder mehr) kann das Skript sehr viele Seiten abrufen, also die Pause nicht zu klein wählen.
