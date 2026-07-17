# Deep Research Agent

Ein intelligenter Recherche-Assistent, der zu beliebigen Themen eigenständig tiefgehende Analysen durchführt. Im Gegensatz zu einfachen Suchagenten **liest** dieser Agent die gefundenen Quellen wirklich und fasst sie per LLM zusammen.

## Features

- **Deep Dive Reading**: Scraped und liest Webseiten vollständig (nicht nur Snippets!)
- **LLM-Zusammenfassung**: Extrahierte Texte werden intelligent auf ~4000 Zeichen zusammengefasst
- **Multi-Aspekt-Recherche**: Zerlegt Themen automatisch in 4 Such-Dimensionen
- **Live-Recherche**: Echtzeit-Suche via DuckDuckGo (kostenlos, kein API Key nötig)
- **Strukturierte Berichte**: Professionelle Markdown-Berichte mit Quellenangaben
- **Moderne UI**: Gradio ChatInterface mit Streaming-Support

## Wie es funktioniert

```
┌─────────────────────────────────────────────────────────────────┐
│                      Deep Research Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PLANNER PHASE                                                │
│     User Query → Generiere 4 Such-Aspekte                       │
│                                                                  │
│  2. EXECUTION PHASE (pro Aspekt)                                │
│     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│     │   Suche      │ → │  Selektiere  │ → │  Deep Read   │   │
│     │  DuckDuckGo  │    │  Top 2-3 URLs │    │  + Summarize │   │
│     └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                                  │
│  3. SYNTHESE PHASE                                               │
│     Aggregiere Zusammenfassungen → Finaler Bericht              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Voraussetzungen

- Python 3.12.10 oder höher
- OpenAI API Key ([Hier erhalten](https://platform.openai.com/api-keys))
- Internetverbindung

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/DEIN-USERNAME/deep-research-agent.git
cd deep-research-agent
```

### 2. Virtuelle Umgebung erstellen & aktivieren

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. API Key konfigurieren

```bash
# Kopiere die Vorlage
cp .env.example .env    # Linux/Mac
copy .env.example .env  # Windows

# Öffne .env und trage deinen OpenAI API Key ein
```

## Verwendung

### Server starten

```bash
python app.py
```

Die Anwendung startet auf `http://localhost:7860`

### Recherche durchführen

1. Öffne `http://localhost:7860` im Browser
2. Gib ein Thema ein (z.B. "Nvidia Aktie Analyse")
3. Der Agent:
   - Zerlegt das Thema in 4 Such-Aspekte
   - Sucht pro Aspekt via DuckDuckGo
   - Liest die Top 2-3 URLs pro Aspekt (Deep Reading)
   - Fasst jeden Artikel per LLM zusammen
   - Erstellt einen umfassenden Bericht mit Quellen

### Beispiel-Themen

- "Nvidia Aktie - aktuelle Entwicklung und Prognose"
- "Künstliche Intelligenz in Deutschland 2025"
- "Bitcoin Kursentwicklung und Zukunftsaussichten"
- "Elektroautos Marktentwicklung Europa"

## Projektstruktur

```
deep-research-agent/
├── app.py              # Gradio Frontend
├── agent.py            # Pydantic AI Agent mit Deep Dive Logik
├── tools.py            # DuckDuckGo Search + LLM Summarization
├── scraper.py          # Web Scraper mit trafilatura
├── requirements.txt    # Python Dependencies
├── .env.example        # Vorlage für Umgebungsvariablen
├── .gitignore          # Git Ignore Regeln
├── AGENTS.md           # Dokumentation für KI-Assistenten
└── README.md           # Diese Datei
```

## Komponenten

| Datei | Beschreibung |
|-------|--------------|
| `app.py` | Gradio ChatInterface mit Streaming-Support |
| `agent.py` | Pydantic AI Agent mit `search_web` und `deep_read_url` Tools |
| `tools.py` | DuckDuckGo-Suche + `summarize_text` für LLM-Zusammenfassung |
| `scraper.py` | Async Web Scraper mit httpx + trafilatura für Textextraktion |

## Tech Stack

| Technologie | Verwendung |
|-------------|------------|
| **Python 3.12** | Programmiersprache |
| **Pydantic AI** | Agent Framework |
| **Gradio** | Web UI |
| **OpenAI GPT-4o-mini** | LLM für Analyse & Zusammenfassung |
| **DuckDuckGo (ddgs)** | Kostenlose Web-Suche |
| **trafilatura** | Haupttext-Extraktion aus HTML |
| **httpx** | Async HTTP Client |

## Konfiguration

### Modell wechseln

In `agent.py`:
```python
model_name: str = "openai:gpt-4o"  # Für bessere Qualität
```

### Scraper-Einstellungen

In `scraper.py`:
```python
WebScraper(
    timeout=15,           # Timeout pro URL
    max_retries=2,        # Wiederholungsversuche
    min_text_length=100   # Mindestlänge für gültigen Content
)
```

### Such-Einstellungen

In `tools.py`:
```python
DuckDuckGoSearchTool(
    timeout=20,      # Timeout für Suche
    max_retries=2,   # Wiederholungsversuche
)
```

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| "OPENAI_API_KEY ist nicht gesetzt" | `.env` Datei prüfen, Key ohne Anführungszeichen |
| Scraping-Fehler bei bestimmten URLs | Normal bei Paywalls/Bot-Schutz, Agent nutzt andere URLs |
| DuckDuckGo Timeout | Internetverbindung prüfen, später erneut versuchen |
| Port 7860 belegt | In `app.py` anderen Port setzen |

## Lizenz

MIT License - Frei verwendbar für private und kommerzielle Zwecke.

## Beitragen

Pull Requests sind willkommen! Für größere Änderungen bitte erst ein Issue erstellen.
