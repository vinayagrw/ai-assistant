import aiohttp
from app.config.search_config import SEARCH_PROVIDERS, SEARCH_PROVIDER_PRIORITY,SEARCH_CONFIG
from app.models.schemas import QueryResponse, Source
from typing import List, Dict
from app.utils.logger import logger, log_execution_time
from app.config.prompt import PROMPTS

class InternetSearch:
    def __init__(self, search_providers):
        self.search_providers = search_providers
        self.timeout = SEARCH_CONFIG["timeout"]
        self.cache = {}


    @log_execution_time
    async def process_internet_query(self, query: str) -> QueryResponse:
        """Process a query using internet search with multiple providers"""
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            logger.info("Using cached results")
            return self.cache[cache_key]

        try:
            logger.info(f"Processing query: {query}")
            
            # Try each provider in priority order
            results = []
            for provider_name in SEARCH_PROVIDER_PRIORITY:
                provider_config = self.search_providers[provider_name]
                if provider_config["enabled"]:
                    logger.info(f"Attempting search with {provider_name}")
                    if provider_name == "serpapi":
                        results = await self._search_with_serpapi(query)
                    elif provider_name == "duckduckgo":
                        results = await self._search_with_duckduckgo(query)
                    
                    if results:
                        break

            if not results:
                logger.warning("No results found from any search provider")
                return QueryResponse(
                    answer="I couldn't find any relevant information.",
                    sources=[],
                    confidence_score=0.0,
                    used_internet_search=True
                )

            logger.info(f"Found {len(results)} results")
            sources = [
                Source(
                    title=result["title"],
                    url=result["link"],
                    content=result["body"],
                    relevance_score=1.0
                )
                for result in results
            ]

            # Step 1: Try to extract a direct answer from sources
            direct_answer = self._extract_answer_from_sources(query, sources)
            if direct_answer:
                logger.info("Found direct answer from sources")
                return QueryResponse(
                    answer=direct_answer,
                    sources=sources,
                    confidence_score=0.9,
                    used_internet_search=True
                )

            # Step 2: Try with structured prompt
            logger.info("No direct answer found, trying with structured prompt")
            context = "\n".join([f"Title: {s.title}\nContent: {s.content}" for s in sources])
            system_prompt, prompt = PROMPTS["structured"], PROMPTS["documentation"].format(context=context, query=query)
            
            # Log the prompt being sent to the model
            logger.info(f"Sending prompt to model:")
            logger.info(f"System prompt: {system_prompt}")
            logger.info("User prompt:")
            logger.info("-" * 80)
            logger.info(prompt)
            logger.info("-" * 80)
            
            answer = self._generate_response(prompt, system_prompt)
            
            # Step 3: Check if the answer is valid
            if any(phrase in answer.lower() for phrase in [
                "if the information is available",
                "based on the given information",
                "provide direct answers",
                "do not repeat instructions",
                "answer questions directly",
                "respond with only",
                "give only the factual",
                "you are a helpful assistant"
            ]):
                logger.info("Model returned instructions, using fallback strategy")
                # Use a combination of approaches for fallback
                fallback_answer = None
                
                # Try to find the most relevant sentence using content scoring
                scored_sentences = []
                for source in sources:
                    sentences = [s.strip() for s in source.content.split('.') if s.strip()]
                    for sentence in sentences:
                        if query.lower() in sentence.lower():
                            # Score the sentence based on content quality
                            score = 0
                            sentence_length = len(sentence.split())
                            if 5 <= sentence_length <= 30:
                                score += 2
                            proper_nouns = sum(1 for word in sentence.split() if word[0].isupper())
                            if proper_nouns > 0:
                                score += min(proper_nouns, 3)
                            if score > 0:
                                scored_sentences.append((sentence, score))
                
                if scored_sentences:
                    scored_sentences.sort(key=lambda x: x[1], reverse=True)
                    fallback_answer = scored_sentences[0][0] + '.'
                else:
                    # Use the first sentence from the most relevant source
                    for source in sources:
                        if source.content:
                            sentences = [s.strip() for s in source.content.split('.') if s.strip()]
                            if sentences:
                                fallback_answer = sentences[0] + '.'
                                break
                
                answer = fallback_answer

            # Cache the results
            response = QueryResponse(
                answer=answer,
                sources=sources,
                confidence_score=0.8,
                used_internet_search=True
            )
            self.cache[cache_key] = response

            logger.info("Response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Error processing internet query: {str(e)}")
            return QueryResponse(
                answer="I'm having trouble searching the internet right now. Please try again in a few moments.",
                sources=[],
                confidence_score=0.0,
                used_internet_search=True
            )
    async def _search_with_serpapi(self, query: str) -> List[Dict]:
            """Search using SerpAPI"""
            provider_config = self.search_providers["serpapi"]
            if not provider_config["api_key"]:
                logger.warning("SerpAPI key not found")
                return []

            try:
                params = {
                    'api_key': provider_config["api_key"],
                    'engine': provider_config["engine"],
                    'q': query,
                    'num': provider_config["num"],
                    'gl': provider_config["gl"],
                    'hl': provider_config["hl"]
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        provider_config["base_url"],
                        params=params,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []
                            
                            # Extract organic results
                            if 'organic_results' in data:
                                for result in data['organic_results']:
                                    results.append({
                                        "title": result.get("title", ""),
                                        "link": result.get("link", ""),
                                        "body": result.get("snippet", "")
                                    })
                            
                            return results
                        else:
                            logger.error(f"SerpAPI error: {response.status}")
                            return []

            except Exception as e:
                logger.error(f"Error in SerpAPI search: {str(e)}")
                return []        
    def _extract_answer_from_sources(self, query: str, sources: List[Source]) -> str:
        """Extract a direct answer from sources using dynamic content scoring"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score each sentence based on relevance
        scored_sentences = []
        
        for source in sources:
            # Split into sentences while preserving original case
            sentences = [s.strip() for s in source.content.split('.') if s.strip()]
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                score = 0
                
                # Exact query match (highest weight)
                if query_lower in sentence_lower:
                    score += 10
                
                # Word overlap with query
                sentence_words = set(sentence_lower.split())
                word_overlap = len(query_words.intersection(sentence_words))
                score += word_overlap * 2
                
                # Content quality scoring
                # Prefer sentences that are:
                # - Not too short (likely incomplete)
                # - Not too long (likely verbose)
                # - Contain proper nouns (likely more specific)
                # - Have good word density
                sentence_length = len(sentence.split())
                if 5 <= sentence_length <= 30:  # Ideal sentence length
                    score += 2
                elif sentence_length < 5:  # Too short
                    score -= 1
                elif sentence_length > 30:  # Too long
                    score -= 1
                
                # Check for proper nouns (words starting with capital letters)
                proper_nouns = sum(1 for word in sentence.split() if word[0].isupper())
                if proper_nouns > 0:
                    score += min(proper_nouns, 3)  # Cap at 3 points
                
                # Check for word density (unique words vs total words)
                unique_words = len(set(sentence_lower.split()))
                if sentence_length > 0:
                    density = unique_words / sentence_length
                    if 0.6 <= density <= 0.8:  # Good word density
                        score += 1
                
                if score > 0:
                    scored_sentences.append((sentence, score))
        
        # Sort by score and return the best match
        if scored_sentences:
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            best_sentence = scored_sentences[0][0]
            return best_sentence + '.'
        
        return None