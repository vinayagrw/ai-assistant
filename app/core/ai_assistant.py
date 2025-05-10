import os
from typing import List, Dict
import requests
from duckduckgo_search import DDGS
import time
from pathlib import Path
import chromadb
from chromadb.config import Settings
from app.models.schemas import QueryResponse, Source
from app.utils.logger import logger, log_execution_time
import numpy as np
from numpy.linalg import norm
import asyncio
from concurrent.futures import ThreadPoolExecutor
import random
import aiohttp
from app.config.search_config import SEARCH_PROVIDERS, SEARCH_PROVIDER_PRIORITY, SEARCH_CONFIG
from app.config.model_config import (
    MODEL_PRIORITY, MODEL_PARAMS, OLLAMA_CONFIG,
    VECTOR_DB_CONFIG, 
)
from app.config.prompt import PROMPTS
from app.core.duplo_related import DuploRelated
from app.core.internet_search import InternetSearch
from app.core.rag import RAG

class AIAssistant:
    def __init__(self):
        """Initialize the AI Assistant with necessary components"""
        logger.info("Initializing AI Assistant components")
        self.model_name = None
        # Initialize Ollama client
        self.ollama_base_url = OLLAMA_CONFIG["base_url"]
        self.docs_path = "docs/"
        self.model_priority = MODEL_PRIORITY
        self.vector_db_path = VECTOR_DB_CONFIG["path"]
        self.max_retries = SEARCH_CONFIG["max_retries"]
        self.retry_delay = SEARCH_CONFIG["retry_delay"]
        self.timeout = SEARCH_CONFIG["timeout"]
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.cache = {}
        
        # Initialize search providers from config
        self.search_providers = SEARCH_PROVIDERS

        self._initialize_components()
        logger.info(f"AI Assistant initialization complete using model: {self.model_name}")

    def _initialize_components(self):
        """Initialize all components with proper error handling"""
        try:
            # First check Ollama availability
            self._check_ollama_availability()
            
            # Then select and pull model
            self.model_name = self._select_best_model()
            if not self._is_model_available(self.model_name):
                logger.info(f"Model {self.model_name} not found, pulling it...")
                self._pull_model()
            
            # Load documentation
            self.documentation = self._load_documentation()
            
            # Initialize vector database
            self._initialize_vector_db()
            
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            raise


        # Initialize DuploRelated and InternetSearch
        self.duplo_related = DuploRelated(self.collection)  # Assuming self.collection is defined
        self.internet_search = InternetSearch(SEARCH_PROVIDERS)

        # Initialize RAG
        self.rag = RAG(self.collection, self.documentation, self.executor)

    def _initialize_vector_db(self):
        """Initialize the vector database and store document embeddings"""
        try:
            logger.info("Initializing vector database...")
            # Create vector DB directory if it doesn't exist
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Initialize Chroma client
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(allow_reset=True)
            )
            
            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=VECTOR_DB_CONFIG["collection_name"],
                metadata={"hnsw:space": "cosine"}
            )
            
            # Check if collection is empty
            if self.collection.count() == 0:
                logger.info("Vector database is empty, storing document embeddings...")
                self._store_document_embeddings()
            else:
                logger.info("Vector database already contains document embeddings")
                
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            raise    
    def _is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                available_models = [model['name'] for model in response.json().get('models', [])]
                return model_name in available_models
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {str(e)}")
            return False

    def _check_ollama_availability(self):
        """Check if Ollama is running and accessible"""
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError("Ollama server is not running")
        except requests.exceptions.ConnectionError:
            error_msg = (
                "Ollama server is not running. Please start it with: "
                "ollama serve"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg)
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            raise

    def _pull_model(self):
        """Pull the model from Ollama with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Pulling model {self.model_name} (attempt {attempt + 1}/{max_retries})...")
                response = requests.post(
                    f"{self.ollama_base_url}/api/pull",
                    json={"name": self.model_name},
                    timeout=30  # Increased timeout for model pulling
                )
                if response.status_code == 200:
                    logger.info(f"Successfully pulled model {self.model_name}")
                    return
                
                # If pulling the preferred model fails, try the next one
                for model in self.model_priority:
                    if model != self.model_name:
                        try:
                            logger.info(f"Trying to pull alternative model: {model}")
                            response = requests.post(
                                f"{self.ollama_base_url}/api/pull",
                                json={"name": model},
                                timeout=30
                            )
                            if response.status_code == 200:
                                self.model_name = model
                                logger.info(f"Successfully pulled alternative model {model}")
                                return
                        except Exception:
                            continue
                            
            except Exception as e:
                logger.error(f"Error pulling model (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise Exception("Failed to pull any model")       
 

    def _select_best_model(self) -> str:
        """Select the best available model based on priority"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                available_models = [model['name'] for model in response.json().get('models', [])]
                for model in self.model_priority:
                    if model in available_models:
                        logger.info(f"Selected model: {model}")
                        return model

            return self.model_priority[0]
        except Exception as e:
            logger.error(f"Error selecting model: {str(e)}")
            return self.model_priority[0]


    def _initialize_vector_db(self):
        """Initialize the vector database and store document embeddings"""
        try:
            logger.info("Initializing vector database...")
            # Create vector DB directory if it doesn't exist
            os.makedirs(self.vector_db_path, exist_ok=True)
            
            # Initialize Chroma client
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_db_path,
                settings=Settings(allow_reset=True)
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name=VECTOR_DB_CONFIG["collection_name"],
                metadata={"hnsw:space": "cosine"}
            )
            
            if self.collection.count() == 0:
                logger.info("Vector database is empty, storing document embeddings...")
                self._store_document_embeddings()
            else:
                logger.info("Vector database already contains document embeddings")
                
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            raise

    def _store_document_embeddings(self):
        """Store document embeddings in the vector database"""
        try:
            for doc in self.documentation:
                # Create document chunks (simple splitting by paragraphs)
                chunks = doc['content'].split('\n\n')
                chunk_ids = [f"{doc['title']}_{i}" for i in range(len(chunks))]
                
                # Store chunks in vector database
                self.collection.add(
                    ids=chunk_ids,
                    documents=chunks,
                    metadatas=[{
                        'title': doc['title'],
                        'path': doc['path'],
                        'chunk_index': i
                    } for i in range(len(chunks))]
                )
                logger.info(f"Stored embeddings for document: {doc['title']}")
                
        except Exception as e:
            logger.error(f"Error storing document embeddings: {str(e)}")
            raise

    def _load_documentation(self) -> List[Dict]:
        """Load and process documentation files"""
        logger.info(f"Loading documentation from {self.docs_path}")
        docs = []
        
        try:
            docs_dir = Path(self.docs_path)
            if not docs_dir.exists():
                logger.warning(f"Documentation directory {self.docs_path} does not exist")
                return docs

            logger.info(f"Scanning directory: {docs_dir.absolute()}")
            for file_path in docs_dir.rglob("*"):
                logger.debug(f"Found file: {file_path}")
                if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            doc_info = {
                                'title': file_path.stem,
                                'path': str(file_path.relative_to(docs_dir)),
                                'content': content
                            }
                            docs.append(doc_info)
                            logger.info(f"Loaded documentation from {file_path} (size: {len(content)} bytes)")
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
                        continue

            logger.info(f"Successfully loaded {len(docs)} documentation files")
            for doc in docs:
                logger.debug(f"Loaded doc: {doc['title']} from {doc['path']}")
            return docs
        except Exception as e:
            logger.error(f"Error loading documentation: {str(e)}")
            return docs


    async def _search_with_duckduckgo(self, query: str) -> List[Dict]:
        """Search using DuckDuckGo"""
        provider_config = self.search_providers["duckduckgo"]
        for attempt in range(self.max_retries):
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(
                        query,
                        region=provider_config["region"],
                        safesearch=provider_config["safesearch"],
                        max_results=provider_config["max_results"]
                    ))
                    results = [
                        {
                            "title": result.get("title", ""),
                            "link": result.get("link", ""),
                            "body": result.get("body", "")
                        }
                        for result in search_results
                    ]
                    logger.info(f"DuckDuckGo search results for query '{query}':")
                    for idx, result in enumerate(results, 1):
                        logger.info(f"Result {idx}:")
                        logger.info(f"  Title: {result['title']}")
                        logger.info(f"  Link: {result['link']}")
                        logger.info(f"  Body: {result['body'][:200]}...")  # Log first 200 chars of body
                    return results
            except Exception as e:
                logger.error(f"Error in DuckDuckGo search: {str(e)}")
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    if attempt < self.max_retries - 1:
                        wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                        logger.warning(f"Rate limit hit, waiting {wait_time:.2f}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                elif attempt < self.max_retries - 1:
                    continue
                return []
        return []

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

    @log_execution_time
    async def process_query(self, query: str) -> QueryResponse:
        """Process a user query and return a response with sources"""
        try:
            logger.info(f"Processing query: {query}")
            if self.duplo_related.is_duplo_related(query):
                logger.info("Query appears to be DuploCloud related, using documentation")
                response = await self.rag.process_documentation_query(query)
            else:
                logger.info("Query appears to be general knowledge, using internet search")
                response = await self.internet_search.process_internet_query(query)

            # Ensure the response is a QueryResponse object
            if not isinstance(response, QueryResponse):
                logger.error("Response is not a valid QueryResponse object")
                return QueryResponse(
                    answer="An error occurred while processing your query.",
                    sources=[],
                    confidence_score=0.0,
                    used_internet_search=False
                )

            return response
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return QueryResponse(
                answer="An error occurred while processing your query.",
                sources=[],
                confidence_score=0.0,
                used_internet_search=False
            )  

    async def _query_ollama(self, model: str, prompt: str) -> str:
        """Query Ollama model"""
        try:
            logger.info(f"Sending prompt to Ollama model '{model}':")
            logger.info(f"Prompt: {prompt}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{OLLAMA_CONFIG['base_url']}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        **MODEL_PARAMS[model]
                    },
                    timeout=OLLAMA_CONFIG["timeout"]
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        logger.info(f"Received response from Ollama model '{model}':")
                        logger.info(f"Response: {response_text[:500]}...") 
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Error from Ollama API: {error_text}")
                        return ""
        except Exception as e:
            logger.error(f"Error querying Ollama model {model}: {str(e)}")
            return ""

    async def _query_ollama_with_retry(self, model: str, prompt: str, max_retries: int = 3) -> str:
        """Query Ollama model with retry logic"""
        for attempt in range(max_retries):
            try:
                response = await self._query_ollama(model, prompt)
                if response:
                    return response
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                    logger.warning(f"Retrying Ollama query for model {model} after {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1} for model {model}: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt + random.uniform(0, 1), 10)
                    await asyncio.sleep(wait_time)
        return "" 