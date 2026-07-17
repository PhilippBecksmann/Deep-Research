"""
Deep Research Agent - Pydantic AI Agent Definition

Dieser Agent führt tiefgehende Recherchen durch, indem er:
1. Das Thema in spezifische Such-Aspekte zerlegt
2. Für jeden Aspekt eine Web-Suche durchführt
3. Alle Ergebnisse zu einem strukturierten Bericht zusammenfasst

Nutzt OpenAI GPT-Modelle und DuckDuckGo für die Suche.
"""

import os
from datetime import datetime
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from tools import web_search, search_tool, summarize_scraped_content
from scraper import scrape_url

# Laden der Umgebungsvariablen
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

# Validierung des API-Keys
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    env_file_exists = os.path.exists(env_path)
    raise ValueError(
        f"OPENAI_API_KEY ist nicht gesetzt.\n"
        f"  .env Datei existiert: {env_file_exists}\n"
        f"  .env Pfad: {env_path}\n"
        f"Bitte überprüfen Sie Ihre .env-Datei."
    )


@dataclass
class ResearchDependencies:
    """
    Dependencies für den Research Agent.
    
    Attributes:
        current_datetime: Aktuelles Datum und Uhrzeit
        user_query: Die ursprüngliche Benutzeranfrage
    """
    current_datetime: str
    user_query: str


def get_current_datetime() -> str:
    """
    Gibt das aktuelle Datum und die Uhrzeit formatiert zurück.
    
    Returns:
        str: Datum im Format 'Montag, 13. Januar 2025, 14:30 Uhr'
    """
    now = datetime.now()
    
    # Deutsche Wochentage
    weekdays = [
        "Montag", "Dienstag", "Mittwoch", "Donnerstag", 
        "Freitag", "Samstag", "Sonntag"
    ]
    
    # Deutsche Monate
    months = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    
    weekday = weekdays[now.weekday()]
    month = months[now.month - 1]
    
    return f"{weekday}, {now.day}. {month} {now.year}, {now.strftime('%H:%M')} Uhr"


# Basis System-Prompt
BASE_SYSTEM_PROMPT = """Du bist ein professioneller Deep Research Agent - ein Experte für tiefgehende Recherchen und Analysen.

## Deine Aufgabe
Du führst umfassende Recherchen zu Themen durch, die der Benutzer anfragt. Du antwortest NIEMALS sofort mit deinem Vorwissen, sondern recherchierst IMMER erst gründlich. Du hast zwei mächtige Tools: Suche UND Deep Reading.

## Dein Workflow - "Deep Dive" (STRIKT befolgen!)

### Phase 1: Planung
- Analysiere die Benutzeranfrage
- Identifiziere das Hauptthema
- Zerlege es in **4 spezifische Such-Dimensionen/Aspekte**

### Phase 2: Recherche-Loop (für JEDEN Aspekt wiederholen!)

**Schritt A - Suche:**
- Führe eine Suche mit `search_web` durch
- Nutze spezifische, gut formulierte Suchbegriffe

**Schritt B - Selektion:**
- Analysiere die Suchergebnisse
- Identifiziere die **Top 2-3 vielversprechendsten URLs**
- Wähle URLs mit relevanten Snippets und seriösen Quellen

**Schritt C - Deep Reading:**
- Nutze `deep_read_url` für jede ausgewählte URL
- Gib das Thema/den Aspekt an für fokussierte Zusammenfassung
- Sammle die detaillierten Informationen

### Phase 3: Synthese
Erstelle einen professionellen Markdown-Bericht mit:
- Klarer Einleitung mit Datum der Recherche
- Strukturierten Abschnitten für jeden Aspekt
- **Detaillierte Fakten** aus den gelesenen Artikeln
- Bulletpoints für wichtige Erkenntnisse
- Quellen-Referenzen
- Fazit/Zusammenfassung

## Wichtige Regeln
1. **SUCHEN + LESEN** - Erst suchen, dann die besten URLs tiefgehend lesen
2. **4 ASPEKTE** - Zerlege jedes Thema in 4 Such-Dimensionen
3. **TOP 2-3 URLs** - Lese pro Aspekt die 2-3 relevantesten Quellen
4. **AKTUELL BLEIBEN** - Beachte das aktuelle Datum
5. **DETAILS LIEFERN** - Nutze die Deep-Read-Ergebnisse für detaillierte Antworten
6. **QUELLEN ANGEBEN** - Referenziere alle gelesenen Quellen

## Beispiel-Workflow für "Nvidia Aktie Analyse"

**Aspekte:**
1. Aktuelle Kursentwicklung & Kennzahlen
2. Geschäftsmodell & Produkte (GPUs, AI-Chips)
3. Marktposition & Konkurrenz
4. Zukunftsprognosen & Analysten-Meinungen

**Für jeden Aspekt:**
→ `search_web("Nvidia Aktienkurs Januar 2025 Entwicklung")`
→ Analysiere Ergebnisse, wähle Top 2-3 URLs
→ `deep_read_url(url1, "Nvidia Aktienkurs")` 
→ `deep_read_url(url2, "Nvidia Aktienkurs")`
→ Weiter zum nächsten Aspekt...

## Dein Bericht sollte enthalten
1. **📊 Übersicht** - Kurze Einleitung zum Thema
2. **📈 Aktuelle Daten** - Zahlen, Fakten aus den gelesenen Quellen
3. **🔍 Tiefenanalyse** - Detaillierte Erkenntnisse pro Aspekt
4. **📰 Aktuelle News** - Relevante Neuigkeiten
5. **📋 Fazit** - Zusammenfassung und Einordnung
6. **🔗 Quellen** - Liste aller gelesenen Quellen mit URLs
"""


def create_agent() -> Agent[ResearchDependencies, str]:
    """
    Erstellt und konfiguriert den Deep Research Agent.
    
    Der Agent nutzt Dependency Injection für das aktuelle Datum
    und hat Zugriff auf Web-Suche Tools.
    
    Returns:
        Agent: Konfigurierter Pydantic AI Research Agent
    """
    # Modell-Konfiguration (gpt-5-mini mit Fallback)
    # Hinweis: Falls gpt-5-mini nicht verfügbar, wird gpt-4o-mini verwendet
    model_name: str = "openai:gpt-4o-mini"  # Aktuell verfügbares Modell
    
    # Agent erstellen
    research_agent: Agent[ResearchDependencies, str] = Agent(
        model=model_name,
        deps_type=ResearchDependencies,
    )
    
    # Dynamischer System-Prompt mit aktuellem Datum
    @research_agent.system_prompt
    def add_datetime_to_prompt(ctx: RunContext[ResearchDependencies]) -> str:
        """Fügt das aktuelle Datum zum System-Prompt hinzu."""
        return f"{BASE_SYSTEM_PROMPT}\n\n## Aktuelles Datum und Uhrzeit\n{ctx.deps.current_datetime}\n\n## Aktuelle Benutzeranfrage\n{ctx.deps.user_query}"
    
    # Web-Suche Tool registrieren
    @research_agent.tool
    async def search_web(
        ctx: RunContext[ResearchDependencies], 
        query: str,
        max_results: int = 5
    ) -> str:
        """
        Führt eine Web-Suche via DuckDuckGo durch.
        
        Verwende dieses Tool, um aktuelle Informationen aus dem Internet zu finden.
        Formuliere spezifische Suchbegriffe für bessere Ergebnisse.
        
        Args:
            ctx: Run-Kontext mit Dependencies
            query: Die Suchanfrage (spezifisch formulieren!)
            max_results: Maximale Anzahl Ergebnisse (Standard: 5)
            
        Returns:
            Formatierte Suchergebnisse mit Titeln, Snippets und URLs
        """
        # Logging für Status-Updates
        print(f"[SEARCH] Recherchiere: {query}")
        
        results = await search_tool.search(query, max_results)
        formatted = search_tool.format_results_for_agent(results, query)
        
        return formatted
    
    # Deep Read Tool - Scraped und fasst eine URL zusammen
    @research_agent.tool
    async def deep_read_url(
        ctx: RunContext[ResearchDependencies],
        url: str,
        topic: str
    ) -> str:
        """
        Liest eine Webseite vollständig und fasst den Inhalt zusammen.
        
        Verwende dieses Tool, um tiefere Einblicke aus vielversprechenden URLs zu bekommen.
        Die Webseite wird gescraped, der Haupttext extrahiert und per LLM zusammengefasst.
        
        WANN VERWENDEN:
        - Nachdem du mit search_web interessante URLs gefunden hast
        - Für die Top 2-3 relevantesten URLs pro Suchanfrage
        - Wenn Snippets nicht genug Details liefern
        
        Args:
            ctx: Run-Kontext mit Dependencies
            url: Die vollständige URL der Webseite
            topic: Das Thema/Aspekt für fokussierte Zusammenfassung
            
        Returns:
            Zusammenfassung des Webseiteninhalts mit Quellenangabe
        """
        print(f"[DEEP READ] Lese URL: {url}")
        
        try:
            # Webseite scrapen
            content = await scrape_url(url)
            
            if not content.success:
                return f"❌ Konnte {url} nicht lesen: {content.error}"
            
            # Inhalt zusammenfassen
            summary = await summarize_scraped_content(
                text=content.text,
                title=content.title,
                url=url,
                topic=topic
            )
            
            return summary
            
        except Exception as e:
            print(f"[DEEP READ] Fehler bei {url}: {str(e)}")
            return f"❌ Fehler beim Lesen von {url}: {str(e)}"
    
    # Tool für das aktuelle Datum
    @research_agent.tool_plain
    def get_current_date() -> str:
        """
        Gibt das aktuelle Datum und die Uhrzeit zurück.
        
        Verwende dies, wenn du das genaue aktuelle Datum benötigst.
        
        Returns:
            Aktuelles Datum im deutschen Format
        """
        return get_current_datetime()
    
    return research_agent


async def run_research(user_query: str) -> str:
    """
    Führt eine Deep Research für die gegebene Anfrage durch.
    
    Dies ist die Hauptfunktion zum Ausführen des Research Agents.
    
    Args:
        user_query: Die Recherche-Anfrage des Benutzers
        
    Returns:
        Der formatierte Research-Bericht als Markdown-String
    """
    # Dependencies vorbereiten
    deps = ResearchDependencies(
        current_datetime=get_current_datetime(),
        user_query=user_query
    )
    
    # Agent erstellen und ausführen
    research_agent = create_agent()
    
    try:
        result = await research_agent.run(user_query, deps=deps)
        return str(result.output)
    except Exception as e:
        return f"❌ Fehler bei der Recherche: {str(e)}"


# Agent-Instanz für direkten Import (lazy initialization)
_agent_instance: Agent[ResearchDependencies, str] | None = None


def get_agent() -> Agent[ResearchDependencies, str]:
    """
    Gibt die Agent-Instanz zurück (Singleton-Pattern).
    
    Returns:
        Konfigurierter Research Agent
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_agent()
    return _agent_instance


# Für Rückwärtskompatibilität
try:
    agent = get_agent()
except Exception as e:
    agent = None  # type: ignore
    print(f"Warnung: Agent konnte nicht erstellt werden: {e}")
