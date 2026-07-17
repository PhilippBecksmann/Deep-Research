"""
DuckDuckGo Search Tool für den Deep Research Agent

Dieses Modul stellt Such-Funktionalität via DuckDuckGo bereit.
Keine API-Keys erforderlich.

Zusätzlich: LLM-basierte Zusammenfassung von Texten.
"""

import os
import asyncio
from typing import Any
from dataclasses import dataclass

from ddgs import DDGS
from openai import AsyncOpenAI

# OpenAI Client für Zusammenfassungen
_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    """
    Gibt den OpenAI Client zurück (lazy initialization).
    
    Returns:
        AsyncOpenAI Client-Instanz
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI()
    return _openai_client


@dataclass
class SearchResult:
    """
    Strukturiertes Suchergebnis.
    
    Attributes:
        title: Titel des Suchergebnisses
        url: URL der Quelle
        snippet: Textausschnitt/Beschreibung
    """
    title: str
    url: str
    snippet: str
    
    def __str__(self) -> str:
        """Formatierte String-Repräsentation für den Agent."""
        return f"**{self.title}**\n{self.snippet}\nQuelle: {self.url}"


class DuckDuckGoSearchTool:
    """
    Wrapper-Klasse für DuckDuckGo-Suchen.
    
    Bietet robuste Fehlerbehandlung und formatierte Ergebnisse.
    """
    
    def __init__(self, timeout: int = 20, max_retries: int = 2):
        """
        Initialisiert das Such-Tool.
        
        Args:
            timeout: Timeout in Sekunden für Suchanfragen
            max_retries: Maximale Anzahl an Wiederholungsversuchen
        """
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5
    ) -> list[SearchResult]:
        """
        Führt eine asynchrone DuckDuckGo-Suche durch.
        
        Args:
            query: Suchbegriff/Suchanfrage
            max_results: Maximale Anzahl an Ergebnissen (Standard: 5)
            
        Returns:
            Liste von SearchResult-Objekten
            
        Raises:
            Gibt leere Liste bei Fehlern zurück (robust handling)
        """
        loop = asyncio.get_event_loop()
        
        for attempt in range(self.max_retries + 1):
            try:
                # DuckDuckGo Search ist synchron, daher run_in_executor
                results = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: self._sync_search(query, max_results)
                    ),
                    timeout=self.timeout
                )
                return results
                
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    # Kurze Pause vor erneutem Versuch
                    await asyncio.sleep(1)
                    continue
                return [SearchResult(
                    title="Timeout",
                    url="",
                    snippet=f"Suche nach '{query}' hat zu lange gedauert."
                )]
                
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                return [SearchResult(
                    title="Fehler",
                    url="",
                    snippet=f"Fehler bei der Suche nach '{query}': {str(e)}"
                )]
        
        return []
    
    def _sync_search(self, query: str, max_results: int) -> list[SearchResult]:
        """
        Synchrone Suche (wird im Executor ausgeführt).
        
        Args:
            query: Suchbegriff
            max_results: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von SearchResult-Objekten
        """
        results: list[SearchResult] = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query, 
                    max_results=max_results,
                    region="de-de"  # Deutsche Ergebnisse bevorzugen
                )
                
                for result in search_results:
                    results.append(SearchResult(
                        title=result.get("title", "Kein Titel"),
                        url=result.get("href", result.get("link", "")),
                        snippet=result.get("body", result.get("snippet", ""))
                    ))
                    
        except Exception:
            # Silent fail - gibt leere Liste zurück
            pass
            
        return results
    
    def format_results_for_agent(
        self, 
        results: list[SearchResult],
        query: str
    ) -> str:
        """
        Formatiert Suchergebnisse für den Agent als lesbaren Text.
        
        Args:
            results: Liste von Suchergebnissen
            query: Ursprüngliche Suchanfrage
            
        Returns:
            Formatierter String mit allen Ergebnissen
        """
        if not results:
            return f"Keine Ergebnisse für '{query}' gefunden."
        
        formatted_parts = [f"### Suchergebnisse für: '{query}'\n"]
        
        for i, result in enumerate(results, 1):
            formatted_parts.append(f"\n**{i}. {result.title}**")
            formatted_parts.append(f"{result.snippet}")
            if result.url:
                formatted_parts.append(f"🔗 {result.url}")
            formatted_parts.append("")  # Leerzeile
        
        return "\n".join(formatted_parts)


# Singleton-Instanz für einfachen Import
search_tool = DuckDuckGoSearchTool()


async def web_search(query: str, max_results: int = 5) -> str:
    """
    Convenience-Funktion für Web-Suche.
    
    Nutzt die Singleton-Instanz des Such-Tools.
    
    Args:
        query: Suchbegriff
        max_results: Maximale Anzahl Ergebnisse
        
    Returns:
        Formatierter String mit Suchergebnissen
    """
    results = await search_tool.search(query, max_results)
    return search_tool.format_results_for_agent(results, query)


# ============================================================================
# LLM-basierte Text-Zusammenfassung
# ============================================================================

SUMMARIZE_SYSTEM_PROMPT = """Du bist ein Experte für das Zusammenfassen von Texten.

Deine Aufgabe:
- Fasse den gegebenen Text präzise zusammen
- Fokussiere dich auf die wichtigsten Fakten und Informationen
- Behalte konkrete Zahlen, Daten und Namen bei
- Strukturiere die Zusammenfassung klar und übersichtlich
- Die Zusammenfassung sollte eigenständig verständlich sein

Schreibe in der gleichen Sprache wie der Originaltext (meist Deutsch oder Englisch).
"""


async def summarize_text(
    text: str,
    topic: str,
    max_chars: int = 4000,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Fasst einen langen Text per LLM zusammen.
    
    Verwendet GPT-4o-mini für kosteneffiziente Zusammenfassungen.
    
    Args:
        text: Der zu zusammenfassende Text
        topic: Das Recherche-Thema (für Fokus)
        max_chars: Maximale Länge der Zusammenfassung
        model: OpenAI Modell für die Zusammenfassung
        
    Returns:
        Zusammengefasster Text (max ~4000 Zeichen)
    """
    # Leerer Text
    if not text or len(text.strip()) < 50:
        return "Kein ausreichender Text zum Zusammenfassen vorhanden."
    
    # Kurzer Text braucht keine Zusammenfassung
    if len(text) <= max_chars:
        return text
    
    try:
        client = _get_openai_client()
        
        # Text auf max 15000 Zeichen begrenzen für API-Effizienz
        truncated_text = text[:15000] if len(text) > 15000 else text
        
        user_prompt = f"""Fasse den folgenden Text zusammen. Der Fokus liegt auf dem Thema: "{topic}"

Behalte die wichtigsten Fakten, Zahlen und Aussagen bei. Die Zusammenfassung sollte maximal {max_chars} Zeichen lang sein.

TEXT:
{truncated_text}

ZUSAMMENFASSUNG:"""

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.3,  # Niedrig für präzise Zusammenfassungen
        )
        
        summary = response.choices[0].message.content
        
        if summary:
            print(f"[SUMMARIZE] Text von {len(text)} auf {len(summary)} Zeichen reduziert")
            return summary.strip()
        
        # Fallback bei leerer Antwort
        return text[:max_chars] + "..."
        
    except Exception as e:
        print(f"[SUMMARIZE] Fehler: {str(e)}")
        # Fallback: Einfache Kürzung
        return text[:max_chars] + "..."


async def summarize_scraped_content(
    text: str,
    title: str,
    url: str,
    topic: str
) -> str:
    """
    Fasst gescrapten Web-Content zusammen und formatiert ihn.
    
    Args:
        text: Der extrahierte Webseitentext
        title: Titel der Webseite
        url: URL der Quelle
        topic: Recherche-Thema
        
    Returns:
        Formatierte Zusammenfassung mit Quellenangabe
    """
    summary = await summarize_text(text, topic)
    
    formatted = f"""### {title}

{summary}

**Quelle:** {url}
"""
    return formatted
