"""
Deep Research Agent - Gradio Frontend

Eine moderne Benutzeroberfläche für den Deep Research Agent.
Unterstützt asynchrone Verarbeitung und zeigt Recherche-Status.
"""

import asyncio
from typing import AsyncGenerator

import gradio as gr
import nest_asyncio

# nest_asyncio für stabile Event-Loop-Handhabung
nest_asyncio.apply()

# Agent-Import mit Fehlerbehandlung
try:
    from agent import get_agent, run_research, ResearchDependencies, get_current_datetime
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    IMPORT_ERROR = str(e)
    print(f"[ERROR] Fehler beim Import des Agenten: {e}")
except ValueError as e:
    AGENT_AVAILABLE = False
    IMPORT_ERROR = str(e)
    print(f"[ERROR] Fehler bei der Agent-Konfiguration: {e}")


async def research_handler(
    message: str,
    history: list[dict[str, str]],
) -> str:
    """
    Async Handler für Recherche-Anfragen.
    
    Verarbeitet die Benutzeranfrage und gibt den Research-Bericht zurück.
    
    Args:
        message: Die Recherche-Anfrage des Benutzers
        history: Die Chat-Historie (wird für Kontext verwendet)
        
    Returns:
        Der formatierte Research-Bericht
    """
    if not AGENT_AVAILABLE:
        return (
            "❌ **Agent nicht verfügbar**\n\n"
            f"Fehler: {IMPORT_ERROR}\n\n"
            "Bitte überprüfen Sie:\n"
            "- Ist die `.env` Datei vorhanden?\n"
            "- Ist `OPENAI_API_KEY` korrekt gesetzt?\n"
            "- Sind alle Dependencies installiert? (`pip install -r requirements.txt`)"
        )
    
    if not message.strip():
        return "⚠️ Bitte geben Sie ein Thema für die Recherche ein."
    
    try:
        # Recherche durchführen
        report = await run_research(message)
        return report
        
    except Exception as e:
        return (
            f"❌ **Fehler bei der Recherche**\n\n"
            f"```\n{str(e)}\n```\n\n"
            "Bitte versuchen Sie es erneut oder formulieren Sie Ihre Anfrage anders."
        )


async def streaming_research_handler(
    message: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    Streaming Handler für Recherche-Anfragen.
    
    Zeigt Fortschritt während der Recherche an.
    
    Args:
        message: Die Recherche-Anfrage
        history: Die Chat-Historie
        
    Yields:
        Status-Updates und finaler Bericht
    """
    if not AGENT_AVAILABLE:
        yield (
            "❌ **Agent nicht verfügbar**\n\n"
            f"Bitte überprüfen Sie Ihre Konfiguration."
        )
        return
    
    if not message.strip():
        yield "⚠️ Bitte geben Sie ein Thema für die Recherche ein."
        return
    
    # Status-Nachricht anzeigen
    yield f"🔄 **Starte Deep Research für:** *{message}*\n\n⏳ Analysiere Thema und bereite Suchen vor..."
    
    try:
        # Kleine Pause für UI-Update
        await asyncio.sleep(0.5)
        
        # Recherche durchführen
        report = await run_research(message)
        
        # Finalen Bericht zurückgeben
        yield report
        
    except Exception as e:
        yield (
            f"❌ **Fehler bei der Recherche**\n\n"
            f"```\n{str(e)}\n```\n\n"
            "Bitte versuchen Sie es erneut."
        )


def sync_research_handler(
    message: str,
    history: list[dict[str, str]],
) -> str:
    """
    Synchroner Wrapper für den async Handler.
    
    Wird von Gradio verwendet, wenn async nicht direkt unterstützt wird.
    
    Args:
        message: Die Recherche-Anfrage
        history: Die Chat-Historie
        
    Returns:
        Der Research-Bericht
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Loop läuft bereits (z.B. in Jupyter)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    research_handler(message, history)
                )
                return future.result(timeout=300)  # 5 Minuten Timeout
        else:
            return loop.run_until_complete(research_handler(message, history))
    except RuntimeError:
        return asyncio.run(research_handler(message, history))


def create_interface() -> gr.ChatInterface:
    """
    Erstellt die Gradio ChatInterface für den Deep Research Agent.
    
    Returns:
        gr.ChatInterface: Konfigurierte Chat-Oberfläche
    """
    interface = gr.ChatInterface(
        fn=streaming_research_handler,
        title="🔍 Deep Research Agent",
        description=(
            "**Ihr persönlicher Recherche-Assistent**\n\n"
            "Geben Sie ein Thema ein und ich führe eine tiefgehende Analyse durch:\n"
            "- Automatische Zerlegung in Such-Aspekte\n"
            "- Live-Recherche im Internet via DuckDuckGo\n"
            "- Strukturierter Bericht mit Quellen\n\n"
            "*Beispiel: 'Nvidia Aktie', 'Klimawandel Deutschland 2025', 'KI in der Medizin'*"
        ),
        examples=[
            "Nvidia Aktie - aktuelle Entwicklung und Prognose",
            "Künstliche Intelligenz in Deutschland 2025",
            "Bitcoin Kursentwicklung und Zukunftsaussichten",
            "Elektroautos Marktentwicklung Europa",
            "Erneuerbare Energien aktuelle Trends",
        ],
        fill_height=True,
    )
    
    return interface


def main() -> None:
    """
    Hauptfunktion zum Starten der Gradio-Anwendung.
    """
    print("\n" + "="*60)
    print("[*] Deep Research Agent - Starte...")
    print("="*60)
    
    if not AGENT_AVAILABLE:
        print("\n[!] WARNUNG: Agent konnte nicht initialisiert werden!")
        print("Die Anwendung startet trotzdem, aber Recherchen werden fehlschlagen.")
        print("Bitte ueberpruefen Sie Ihre .env-Datei.\n")
    else:
        print("\n[OK] Agent erfolgreich initialisiert!")
        print("Bereit fuer Deep Research Anfragen.\n")
    
    interface = create_interface()
    
    print("[*] Starte Server auf http://localhost:7860")
    print("="*60 + "\n")
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
