from duckduckgo_search import DDGS

class WebActions:
    @staticmethod
    def search_web(query):
        """Searches the web securely and safely and returns a text summary."""
        print(f"[System] Searching the web securely for: {query}")
        try:
            # We use strict safesearch to ensure results are safe and secure
            results = DDGS().text(query, max_results=3, safesearch='strict')
            if not results:
                return "I couldn't find any relevant and safe information for that query."
            
            # Combine snippets for context
            snippets = [f"- {res['body']}" for res in results]
            summary = "\n".join(snippets)
            return summary
        except Exception as e:
            print(f"[Web Error] {e}")
            return None
