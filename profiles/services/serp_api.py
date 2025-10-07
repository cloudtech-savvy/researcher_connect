import os
import logging
from typing import Dict, Any, List, Optional

import requests

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"


class SerpAPIClient:
    """Minimal SerpAPI client for Google Scholar-like queries.

    Usage:
        client = SerpAPIClient()
        results = client.search_scholar_authors(query="Computer Science Catholic University of America")

    This class reads the API key from the environment variable `SERPAPI_API_KEY`.

    It returns the raw JSON from SerpAPI by default and a small helper to extract author blocks.
    """

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.environ.get("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not set in environment; requests will fail without a key")
        self.session = session or requests.Session()

    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = dict(params)
        params["api_key"] = self.api_key
        try:
            resp = self.session.get(SERPAPI_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("SerpAPI request failed")
            raise

    def search_scholar(self, query: str, num: int = 10) -> Dict[str, Any]:
        """Perform a general Google Scholar search via SerpAPI (scholar engine).

        Returns raw JSON response. The caller can parse `organic_results`, `scholar_results`, etc.
        """
        params = {
            "engine": "google_scholar",
            "q": query,
            "num": num,
        }
        return self._get(params)

    def search_scholar_authors(self, query: str, num: int = 10) -> List[Dict[str, Any]]:
        """Search for authors matching the query and return a list of author-like dicts.

        SerpAPI returns `author_results` or similar fields depending on the engine/response. We
        look for common fields and normalize to a small shape.
        """
        data = self.search_scholar(query=query, num=num)
        results: List[Dict[str, Any]] = []

        # SerpAPI scholar responses often include 'author_results' or 'scholar_results'
        # We'll inspect likely places for author information and normalize.
        if not data:
            return results

        # example potential keys: 'author_results', 'scholar_results', 'organic_results'
        for key in ("author_results", "scholar_results", "organic_results"):  # fallback order
            block = data.get(key)
            if not block:
                continue
            for item in block:
                author = {
                    "name": item.get("author") or item.get("title") or item.get("name"),
                    "affiliation": item.get("affiliation") or item.get("publication") or None,
                    "profile_link": item.get("profile_link") or item.get("link") or None,
                    "snippet": item.get("snippet") or item.get("description") or None,
                    "raw": item,
                }
                results.append(author)
            if results:
                break

        return results

    def get_author_profile(self, author_profile_link: str) -> Dict[str, Any]:
        """Fetch a SerpAPI result page for a specific author profile link.

        Some SerpAPI results include 'author' or 'profile' pages that can be retrieved by
        passing the 'engine': 'google_scholar_author' and 'author_id' or by querying the
        profile URL via the normal search endpoint. This helper tries to be flexible: if the
        provided link contains an 'user=' or 'author=' query param we'll try to extract it and
        use the scholar author engine. Otherwise we call the general search engine with the
        URL to surface possible publication lists.
        """
        # try to extract an author id from the link
        from urllib.parse import urlparse, parse_qs

        parsed = urlparse(author_profile_link)
        q = parse_qs(parsed.query)
        author_id = q.get("user") or q.get("author")
        params: Dict[str, Any] = {}
        if author_id:
            # use the author engine if available
            params = {"engine": "google_scholar_author", "author_id": author_id[0]}
        else:
            # fallback: search the profile URL
            params = {"engine": "google_scholar", "q": author_profile_link}

        return self._get(params)

    def extract_publications(self, scholar_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize publication entries from a scholar response to a simple shape.

        Each returned item will contain: title, year (optional), link (optional), snippet (optional)
        and the raw SerpAPI entry.
        """
        pubs: List[Dict[str, Any]] = []
        if not scholar_response:
            return pubs

        # common sections where publications may live
        for key in ("scholar_results", "organic_results", "inline_people_also_search_for"):
            block = scholar_response.get(key)
            if not block:
                continue
            for item in block:
                title = item.get("title") or item.get("publication") or item.get("snippet")
                # try to parse year from snippet or snippet_metadata
                year = None
                snippet = item.get("snippet") or item.get("description")
                # many scholar items include 'publication_info' with year
                pub_info = item.get("publication_info") or {}
                if isinstance(pub_info, dict):
                    year = pub_info.get("year") or pub_info.get("pub_year")

                # try to find a year in snippet as a 4-digit number
                if not year and snippet:
                    import re

                    m = re.search(r"(19|20)\d{2}", snippet)
                    if m:
                        year = int(m.group(0))

                pub = {
                    "title": title,
                    "year": int(year) if year else None,
                    "link": item.get("link") or item.get("source_url") or None,
                    "snippet": snippet,
                    "raw": item,
                }
                pubs.append(pub)
            if pubs:
                break

        return pubs

    def search_author_publications(self, author: str, profile_link: Optional[str] = None, num: int = 50) -> List[Dict[str, Any]]:
        """Search for an author's publications. Prefer using a profile_link if available; otherwise
        run a scholar query for the author name and university to try to narrow results.
        """
        if profile_link:
            try:
                resp = self.get_author_profile(profile_link)
                return self.extract_publications(resp)
            except Exception:
                logger.exception("Failed to fetch publications via profile link, falling back to query")

        # fallback query includes the author name and an affiliation hint
        query = f"{author} Catholic University of America"
        try:
            resp = self.search_scholar(query=query, num=num)
            return self.extract_publications(resp)
        except Exception:
            logger.exception("Failed to search scholar for author: %s", author)
            return []


# Convenience function for quick use without instantiating the client
def search_authors(query: str, api_key: Optional[str] = None, num: int = 10) -> List[Dict[str, Any]]:
    client = SerpAPIClient(api_key=api_key)
    return client.search_scholar_authors(query=query, num=num)
"""
I want to do  is  Gather the profiles of professors from the
Catholic University of America who published  their work  on Google Scholar and extract relevant information.
 using SerpAPI and store them in a database or csv file.

Then I can use the information in building a web application that allows users to search for professors by department and view their profiles, including their publications and research interests.
"""


