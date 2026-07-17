# Projektanweisungen für KI-Assistenten - Deep Research Agent

## Projektübersicht

Dies ist ein **Deep Research Agent** - ein intelligenter Recherche-Assistent, der:
- Themen automatisch in Such-Aspekte zerlegt
- Live im Internet via DuckDuckGo recherchiert
- Strukturierte Markdown-Berichte mit Quellenangaben erstellt

**Technologie-Stack:**
- **Logic Framework:** Pydantic AI (neueste Version)
- **Frontend:** Gradio ChatInterface
- **LLM:** OpenAI GPT-4o-mini (Fallback-fähig)
- **Search Engine:** DuckDuckGo (kostenlos, kein API Key nötig)
- **Python:** 3.12.10

**Hauptkomponenten:**
- `agent.py`: Pydantic AI Agent mit Deep Research Logik
- `tools.py`: DuckDuckGo Search Tool Implementation
- `app.py`: Gradio ChatInterface mit Streaming-Support
- `requirements.txt`: Alle Dependencies

## Entwicklungsumgebung

### Python-Version
- **WICHTIG**: Wir verwenden ausschließlich Python 3.12.10
- Verwende immer diese Version für alle Python-bezogenen Operationen

### Abhängigkeiten installieren
```bash
# Virtuelle Umgebung erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Umgebungsvariablen
- Die Datei `.env` wird benötigt und MUSS einen `OPENAI_API_KEY` enthalten
- Kopiere `.env.example` zu `.env` und füge deinen Key ein
- Der API-Key wird von `agent.py` beim Import validiert

## Projekt starten

```bash
# Stelle sicher, dass die virtuelle Umgebung aktiviert ist
python app.py
```

- Die Anwendung läuft auf `http://localhost:7860`
- Port kann in `app.py` bei Bedarf geändert werden

## Architektur und Design-Prinzipien

### Modul-Struktur

**tools.py** (Search Engine):
- `DuckDuckGoSearchTool` Klasse für Web-Suchen
- `SearchResult` Dataclass für strukturierte Ergebnisse
- Robuste Fehlerbehandlung mit Timeouts und Retries
- Asynchrone Ausführung via `run_in_executor`

**agent.py** (Backend):
- Definiert den Pydantic AI Research Agent
- Verwendet `ResearchDependencies` für Dependency Injection
- Dynamischer System-Prompt mit aktuellem Datum
- Registriert `search_web` Tool für Internet-Recherche
- Vollständig asynchrone Implementierung

**app.py** (Frontend):
- Gradio `ChatInterface` mit modernem Theme
- Streaming-Handler für Echtzeit-Updates
- Fehlerbehandlung für fehlende Konfiguration
- Custom CSS für bessere UX

### Research Workflow

Der Agent folgt einem strikten Workflow:

1. **Kontext & Datum:** Ermittelt automatisch das aktuelle Datum
2. **Analyse & Zerlegung:** Zerlegt das Thema in 3-4 Such-Aspekte
3. **Recherche (Deep Dive):** Führt für jeden Aspekt eine DuckDuckGo-Suche durch
4. **Synthese:** Erstellt strukturierten Markdown-Bericht mit Quellen

### Dependency Injection

Der Agent nutzt `ResearchDependencies` für Kontext:

```python
@dataclass
class ResearchDependencies:
    current_datetime: str  # Aktuelles Datum für zeitkritische Infos
    user_query: str        # Ursprüngliche Benutzeranfrage
```

Dies wird im System-Prompt verwendet:

```python
@research_agent.system_prompt
def add_datetime_to_prompt(ctx: RunContext[ResearchDependencies]) -> str:
    return f"Aktuelles Datum: {ctx.deps.current_datetime}"
```

### Tool-Entwicklung

Neue Tools werden wie folgt hinzugefügt:

```python
@research_agent.tool
async def my_tool(
    ctx: RunContext[ResearchDependencies], 
    param: str
) -> str:
    """
    Klare Beschreibung des Tools für das LLM.
    
    Args:
        ctx: Run-Kontext mit Dependencies
        param: Beschreibung des Parameters
        
    Returns:
        str: Beschreibung des Rückgabewerts
    """
    # Tool-Logik
    return "Ergebnis"
```

**Wichtig bei Tools:**
- Verwende `@agent.tool` für Tools mit RunContext
- Verwende `@agent.tool_plain` für einfache Tools ohne Kontext
- Docstrings sind WICHTIG - sie helfen dem LLM zu verstehen, wann das Tool verwendet werden soll
- Type Hints sind erforderlich

## Code-Stil und Konventionen

### Python-Konventionen
- Verwende Type Hints für alle Funktionen und Variablen
- Folge PEP 8 Style Guide
- Docstrings im Google-Stil für alle Funktionen
- Explizite Imports (vermeide `import *`)
- Vollständig asynchron (`async`/`await`)

### Naming-Konventionen
- Funktionen und Variablen: `snake_case`
- Klassen: `PascalCase`
- Konstanten: `UPPER_SNAKE_CASE`
- Private Methoden: `_leading_underscore`

### Fehlerbehandlung
- Verwende spezifische Exception-Types
- Gib hilfreiche Fehlermeldungen mit Kontext
- Validiere kritische Inputs (z.B. API-Keys)
- Robuste Timeouts für externe Aufrufe

## Testing und Debugging

### Manuelle Tests
- Teste neue Tools durch direkte Chat-Interaktion
- Beispiel-Prompts in `app.py` aktualisieren, wenn neue Features hinzugefügt werden
- Prüfe die Console-Ausgabe für Recherche-Status (`🔍 Recherchiere: ...`)

### Debug-Informationen
- Agent-Fehler werden in der UI angezeigt
- Console-Output zeigt Recherche-Fortschritt
- Bei API-Problemen: OpenAI API Status überprüfen

## Deployment-Hinweise

### Lokale Entwicklung
- Standard-Port: 7860
- `share=False` in `interface.launch()` für lokale Entwicklung
- `nest_asyncio` für Event-Loop-Stabilität

### Öffentliches Deployment
- Setze `share=True` für temporäre öffentliche URL (Gradio)
- Oder deploye auf Hugging Face Spaces, Railway, etc.
- Stelle sicher, dass OPENAI_API_KEY als Umgebungsvariable gesetzt ist

## Wichtige Dateien

- `requirements.txt`: Python-Abhängigkeiten
- `.env`: Lokale Umgebungsvariablen (NICHT in Git)
- `.env.example`: Vorlage für Umgebungsvariablen
- `.gitignore`: Enthält `.env`, `venv/`, etc.

## Häufige Aufgaben

### System-Prompt ändern
- Ändere `BASE_SYSTEM_PROMPT` in `agent.py`
- Der Prompt sollte klar definieren, wie der Agent recherchiert

### OpenAI-Modell wechseln
- Ändere `model_name` in `create_agent()` in `agent.py`
- Format: `"openai:model-name"` (z.B. `"openai:gpt-4o"`, `"openai:gpt-4o-mini"`)

### Search Tool anpassen
- Ändere Einstellungen in `DuckDuckGoSearchTool` in `tools.py`
- `timeout`: Timeout für Suchanfragen
- `max_retries`: Wiederholungsversuche bei Fehlern
- `region`: Regionale Suchpräferenz (Standard: "de-de")

### UI anpassen
- Ändere `title` und `description` in `create_interface()` in `app.py`
- Aktualisiere `examples` für neue Features
- Passe `custom_css` für Styling an
- Gradio Theme kann mit `theme` Parameter angepasst werden

## Bekannte Einschränkungen

- Der Bot benötigt eine aktive Internetverbindung für:
  - OpenAI API-Aufrufe
  - DuckDuckGo Web-Suchen
- API-Rate-Limits von OpenAI können zu Verzögerungen führen
- DuckDuckGo kann bei zu vielen Anfragen temporär blockieren
- Recherche-Qualität hängt von den Suchbegriffen ab

## Best Practices für Änderungen

1. **Teste lokal**: Stelle sicher, dass der Agent lokal funktioniert
2. **Docstrings**: Alle neuen Funktionen brauchen Docstrings
3. **Type Safety**: Nutze Type Hints konsequent
4. **Error Handling**: Fange Fehler ab und gib hilfreiche Meldungen
5. **Async First**: Alle I/O-Operationen sollten asynchron sein
6. **Separation of Concerns**: 
   - Tools in `tools.py`
   - Agent-Logik in `agent.py`
   - UI-Logik in `app.py`

## Nützliche Befehle

```bash
# Dependencies aktualisieren
pip install --upgrade -r requirements.txt

# Neue Dependency hinzufügen
pip install <package-name>
pip freeze > requirements.txt

# Python-Version überprüfen
python --version  # Sollte 3.12.10 sein

# Code formatieren (optional)
black agent.py app.py tools.py

# Type Checking (optional)
mypy agent.py app.py tools.py
```

## Troubleshooting

### "OPENAI_API_KEY ist nicht gesetzt"
- Überprüfe, dass `.env` Datei existiert
- Stelle sicher, dass der Key korrekt eingetragen ist (ohne Anführungszeichen)
- Starte die Anwendung neu

### "Agent konnte nicht erstellt werden"
- Überprüfe OpenAI API Key Gültigkeit
- Prüfe OpenAI Account Credits
- Überprüfe Internetverbindung

### DuckDuckGo Timeout
- Erhöhe `timeout` in `DuckDuckGoSearchTool`
- Prüfe Internetverbindung
- Warte kurz und versuche es erneut

### Import-Fehler
- Stelle sicher, dass virtuelle Umgebung aktiviert ist
- Installiere Dependencies neu: `pip install -r requirements.txt`

### Port bereits belegt
- Ändere `server_port` in `app.py`
- Oder beende die Anwendung, die Port 7860 verwendet
