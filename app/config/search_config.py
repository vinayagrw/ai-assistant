"""Search provider configuration"""

import os
from typing import Dict, Any

# Search provider configurations
SEARCH_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "serpapi": {
        "enabled": True,
        "api_key": os.getenv("SERPAPI_API_KEY", ""),
        "base_url": "https://serpapi.com/search",
        "engine": "google",
        "num": 3,
        "gl": "us",  # Google country
        "hl": "en"   # Language
    },
    "duckduckgo": {
        "enabled": True,
        "fallback": True,
        "region": "wt-wt",
        "safesearch": "off",
        "max_results": 3
    }
}

# Search provider priority order
SEARCH_PROVIDER_PRIORITY = ["serpapi", "duckduckgo"]

# Search configuration
SEARCH_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,
    "timeout": 10,
    "cache_ttl": 3600  # Cache time-to-live in seconds
} 