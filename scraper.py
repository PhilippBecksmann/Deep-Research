"""
Web Scraper Modul für den Deep Research Agent

Dieses Modul stellt Funktionalität zum Scrapen und Extrahieren
von Haupttext aus Webseiten bereit.

Verwendet trafilatura für saubere Text-Extraktion und httpx für async HTTP.
"""

import asyncio
import random
from typing import Optional
from dataclasses import dataclass

import httpx
import trafilatura


@dataclass
class ScrapedContent:
    """
    Strukturierter Container für gescrapten Inhalt.
    
    Attributes:
        url: Die gescrapte URL
        title: Extrahierter Titel der Seite
        text: Extrahierter Haupttext
        success: Ob das Scraping erfolgreich war
        error: Fehlermeldung falls nicht erfolgreich
    """
    url: str
    title: str
    text: str
    success: bool
    error: Optional[str] = None
    
    def __str__(self) -> str:
        """Formatierte String-Repräsentation."""
        if self.success:
            return f"**{self.title}**\n{self.text[:500]}..."
        return f"Fehler beim Laden von {self.url}: {self.error}"


# User-Agents für bessere Ergebnisse (Browser-Simulation)
USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class WebScraper:
    """
    Async Web Scraper für Haupttext-Extraktion.
    
    Verwendet httpx für HTTP-Requests und trafilatura für Text-Extraktion.
    Bietet robuste Fehlerbehandlung und User-Agent-Rotation.
    """
    
    def __init__(
        self, 
        timeout: int = 15, 
        max_retries: int = 2,
        min_text_length: int = 100
    ):
        """
        Initialisiert den Web Scraper.
        
        Args:
            timeout: Timeout in Sekunden für HTTP-Requests
            max_retries: Maximale Anzahl an Wiederholungsversuchen
            min_text_length: Minimale Textlänge für gültigen Content
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_text_length = min_text_length
    
    def _get_random_user_agent(self) -> str:
        """Gibt einen zufälligen User-Agent zurück."""
        return random.choice(USER_AGENTS)
    
    def _get_headers(self) -> dict[str, str]:
        """Erstellt HTTP-Headers für den Request."""
        return {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    async def fetch_url(self, url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Lädt den HTML-Inhalt einer URL asynchron.
        
        Args:
            url: Die zu ladende URL
            
        Returns:
            Tuple von (HTML-Content, Fehler). Bei Erfolg ist Fehler None.
        """
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    verify=True
                ) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    # Status-Code prüfen
                    if response.status_code == 403:
                        return None, "Zugriff verweigert (403)"
                    elif response.status_code == 404:
                        return None, "Seite nicht gefunden (404)"
                    elif response.status_code >= 400:
                        return None, f"HTTP-Fehler {response.status_code}"
                    
                    # Content-Type prüfen
                    content_type = response.headers.get("content-type", "")
                    if "text/html" not in content_type and "application/xhtml" not in content_type:
                        return None, f"Kein HTML-Content: {content_type}"
                    
                    return response.text, None
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                return None, "Timeout beim Laden der Seite"
                
            except httpx.ConnectError:
                return None, "Verbindung fehlgeschlagen"
                
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                return None, f"Fehler: {str(e)}"
        
        return None, "Maximale Versuche erreicht"
    
    def extract_text(self, html: str, url: str) -> tuple[str, str]:
        """
        Extrahiert den Haupttext aus HTML mit trafilatura.
        
        Args:
            html: Der HTML-Content
            url: Die ursprüngliche URL (für Metadaten)
            
        Returns:
            Tuple von (Titel, Haupttext)
        """
        try:
            # Metadata extrahieren für Titel
            metadata = trafilatura.extract_metadata(html)
            title = ""
            if metadata:
                title = metadata.title or ""
            
            # Haupttext extrahieren
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
                include_links=False,
                deduplicate=True,
                favor_precision=True,
            )
            
            if not text:
                # Fallback: Nur Basis-Extraktion
                text = trafilatura.extract(html)
            
            if not text:
                return title or "Unbekannt", ""
            
            return title or "Unbekannt", text.strip()
            
        except Exception as e:
            return "Fehler", f"Extraktion fehlgeschlagen: {str(e)}"
    
    async def scrape_and_extract(self, url: str) -> ScrapedContent:
        """
        Kombinierte Funktion: Lädt URL und extrahiert Haupttext.
        
        Args:
            url: Die zu scrapende URL
            
        Returns:
            ScrapedContent mit Titel, Text und Status
        """
        print(f"[SCRAPE] Lade: {url}")
        
        # HTML laden
        html, error = await self.fetch_url(url)
        
        if error:
            print(f"[SCRAPE] Fehler bei {url}: {error}")
            return ScrapedContent(
                url=url,
                title="",
                text="",
                success=False,
                error=error
            )
        
        # Text extrahieren
        title, text = self.extract_text(html, url)
        
        # Validierung
        if len(text) < self.min_text_length:
            print(f"[SCRAPE] Zu wenig Text bei {url}: {len(text)} Zeichen")
            return ScrapedContent(
                url=url,
                title=title,
                text=text,
                success=False,
                error=f"Zu wenig Text extrahiert ({len(text)} Zeichen)"
            )
        
        print(f"[SCRAPE] Erfolgreich: {url} ({len(text)} Zeichen)")
        return ScrapedContent(
            url=url,
            title=title,
            text=text,
            success=True
        )
    
    async def scrape_multiple(
        self, 
        urls: list[str], 
        delay: float = 0.5
    ) -> list[ScrapedContent]:
        """
        Scraped mehrere URLs mit kurzer Verzögerung.
        
        Args:
            urls: Liste der zu scrapenden URLs
            delay: Verzögerung zwischen Requests in Sekunden
            
        Returns:
            Liste von ScrapedContent-Objekten
        """
        results: list[ScrapedContent] = []
        
        for i, url in enumerate(urls):
            result = await self.scrape_and_extract(url)
            results.append(result)
            
            # Kurze Pause zwischen Requests (außer beim letzten)
            if i < len(urls) - 1:
                await asyncio.sleep(delay)
        
        return results


# Singleton-Instanz für einfachen Import
scraper = WebScraper()


async def scrape_url(url: str) -> ScrapedContent:
    """
    Convenience-Funktion zum Scrapen einer einzelnen URL.
    
    Args:
        url: Die zu scrapende URL
        
    Returns:
        ScrapedContent mit extrahiertem Text
    """
    return await scraper.scrape_and_extract(url)


async def scrape_urls(urls: list[str]) -> list[ScrapedContent]:
    """
    Convenience-Funktion zum Scrapen mehrerer URLs.
    
    Args:
        urls: Liste der URLs
        
    Returns:
        Liste von ScrapedContent-Objekten
    """
    return await scraper.scrape_multiple(urls)
