from core.base_agent import BaseAgent
from typing import Dict, Any, List
from tavily import TavilyClient
from config.settings import config
import asyncio
from bs4 import BeautifulSoup
import requests

class ResearchAgent(BaseAgent):
    """Agent for web research and information gathering"""
    
    def __init__(self):
        super().__init__(name="research_agent")
        self.tavily_client = TavilyClient(api_key=config.TAVILY_API_KEY)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process research requests"""
        message = input_data.get("message", "")
        
        # Extract search query
        search_query = self._extract_search_query(message)
        
        # Perform research
        research_results = await self.research(search_query)
        
        # Summarize results
        summary = await self.summarize_research(research_results, message)
        
        return {
            "text": summary,
            "metadata": {
                "agent": self.name,
                "sources": [r["url"] for r in research_results[:5]]
            }
        }
    
    async def research(self, query: str) -> List[Dict[str, Any]]:
        """Perform web research using Tavily"""
        try:
            # Search with Tavily
            search_results = await asyncio.to_thread(
                self.tavily_client.search,
                query,
                search_depth="advanced",
                max_results=5
            )
            
            results = []
            for result in search_results.get("results", []):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "content": result.get("content"),
                    "score": result.get("score")
                })
                
            # Additional scraping if needed
            for result in results[:2]:  # Scrape top 2 results
                scraped_content = await self.scrape_url(result["url"])
                if scraped_content:
                    result["full_content"] = scraped_content
                    
            return results
            
        except Exception as e:
            print(f"Research error: {e}")
            return []
    
    async def scrape_url(self, url: str) -> str:
        """Scrape content from URL"""
        try:
            response = await asyncio.to_thread(requests.get, url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to 5000 chars
            
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return ""
    
    async def summarize_research(self, results: List[Dict], query: str) -> str:
        """Summarize research results"""
        if not results:
            return "I couldn't find any relevant information for your query."
            
        # Prepare content for summarization
        combined_content = "\n\n".join([
            f"Source: {r['title']}\n{r.get('full_content', r['content'])[:1000]}"
            for r in results[:3]
        ])
        
        prompt = f"""Based on the following research results for the query "{query}", 
        provide a comprehensive summary:
        
        {combined_content}
        
        Summary:"""
        
        summary = await self.think(prompt)
        
        # Add sources
        sources = "\n\nSources:\n"
        for r in results[:3]:
            sources += f"- [{r['title']}]({r['url']})\n"
            
        return summary + sources
    
    def _extract_search_query(self, message: str) -> str:
        """Extract search query from message"""
        # Remove common phrases
        query = message.lower()
        remove_phrases = ['search for', 'find', 'look up', 'research', 'what is', 'tell me about']
        
        for phrase in remove_phrases:
            query = query.replace(phrase, '')
            
        return query.strip()