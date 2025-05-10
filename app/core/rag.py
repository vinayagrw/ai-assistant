from typing import List, Dict
import time, asyncio
import requests
from pathlib import Path


from app.models.schemas import QueryResponse, Source
from app.utils.logger import logger, log_execution_time
from app.config.prompt import PROMPTS


from app.config.search_config import SEARCH_PROVIDERS, SEARCH_PROVIDER_PRIORITY, SEARCH_CONFIG
from app.config.model_config import (
    MODEL_PRIORITY, MODEL_PARAMS, OLLAMA_CONFIG,
    VECTOR_DB_CONFIG, DUPLO_KEYWORDS
)
class RAG:
    def __init__(self, collection,documentation, executor):
        self.collection = collection
        self.executor = executor
        self.documentation = documentation
        self.model_priority = MODEL_PRIORITY
        self.ollama_base_url = OLLAMA_CONFIG["base_url"]
        self.cache = {}


    def _get_model_params(self, model_name: str) -> dict:
        """Get optimized parameters for specific models"""
        params = MODEL_PARAMS.get(model_name, MODEL_PARAMS["neural-chat"]).copy()
        # Increase timeouts for all models
        params["timeout"] = 30  # 30 seconds timeout for all models
        return params

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

    def _find_relevant_docs(self, query: str, max_docs: int = 1) -> List[Dict]:
        """Find the most relevant documentation for a query using vector search"""
        start_time = time.time()
        
        if not self.documentation:
            logger.warning("No documentation available for search")
            return []

        try:
            logger.info(f"Searching documentation for query: {query}")
            
            # Check cache first
            cache_key = query.lower().strip()
            if cache_key in self.cache:
                logger.info("Using cached results")
                logger.info(f"Cache lookup took {time.time() - start_time:.2f} seconds")
                return self.cache[cache_key]
            
            # First try exact keyword matching for simple queries
            keyword_start = time.time()
            query_lower = query.lower()
            for doc in self.documentation:
                if query_lower in doc['content'].lower():
                    logger.info(f"Found exact match in document: {doc['title']}")
                    self.cache[cache_key] = [doc]
                    logger.info(f"Keyword matching took {time.time() - keyword_start:.2f} seconds")
                    return [doc]
            logger.info(f"Keyword matching (no match) took {time.time() - keyword_start:.2f} seconds")
            

            vector_start = time.time()
            results = self.collection.query(
                query_texts=[query],
                n_results=1  # Only get the most relevant result
            )
            logger.info(f"Vector search took {time.time() - vector_start:.2f} seconds")
            

            relevant_docs = []
            
            if results['ids'][0]:
                doc_id, metadata, distance = (
                    results['ids'][0][0],
                    results['metadatas'][0][0],
                    results['distances'][0][0]
                )
                
                if distance < VECTOR_DB_CONFIG["similarity_threshold"]:  # Only include if similarity is good enough
                    title = metadata['title']
                    doc = next((d for d in self.documentation if d['title'] == title), None)
                    if doc:
                        relevant_docs.append(doc)
                        logger.debug(f"Relevant doc: {title} (distance: {distance:.3f})")
            
            # Cache the results
            self.cache[cache_key] = relevant_docs
            logger.info(f"Total document search took {time.time() - start_time:.2f} seconds")
            logger.info(f"Found {len(relevant_docs)} relevant documents")
            return relevant_docs

        except Exception as e:
            logger.error(f"Error finding relevant docs: {str(e)}")
            return []
        
    def _generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response using Ollama with fallback to other models"""
        start_time = time.time()
        
        # Try each model in sequence - just using phi
        for model in self.model_priority:
            try:
                logger.info(f"Attempting to use model: {model}")
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                # Get model parameters
                params = self._get_model_params(model)
                timeout = params.pop("timeout")

                # Quick health check with increased timeout
                try:
                    health_check = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
                    if health_check.status_code != 200:
                        logger.warning(f"Health check failed for {model}, trying next model")
                        continue
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Health check failed for {model}: {str(e)}, trying next model")
                    continue

                try:
                    response = requests.post(
                        f"{self.ollama_base_url}/api/chat",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": False,
                            "options": params
                        },
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Successfully generated response with {model} in {time.time() - start_time:.2f} seconds")
                        return response.json()['message']['content']
                    else:
                        logger.warning(f"Model {model} returned status code {response.status_code}-{response.text}")
                        continue
                        
                except requests.exceptions.Timeout:
                    logger.warning(f"Timeout while using model {model} after {timeout} seconds")
                    continue
                except Exception as e:
                    logger.warning(f"Error with model {model}: {str(e)}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Failed with model {model}: {str(e)}")
                continue

        # If all models fail, use direct response
        logger.warning("All models failed, using direct response")
        return self._generate_direct_response(prompt, system_prompt or "")
    

    def _generate_direct_response(self, query: str, context: str) -> str:
        """Generate a direct response without using Ollama"""
        try:
            # Clean up the context
            lines = [line.strip() for line in context.split('\n') if line.strip()]
            
            # Skip metadata lines (lines starting with ---)
            content_lines = [line for line in lines if not line.startswith('---')]
            
            content = ' '.join(content_lines)
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            
            # Find the most relevant sentence based on word overlap
            query_words = set(query.lower().split())
            best_sentence = None
            max_overlap = 0
            
            for sentence in sentences:
                if sentence.startswith('#') or '**' in sentence or '[' in sentence:
                    continue
                    
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words.intersection(sentence_words))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_sentence = sentence
            
            if best_sentence:
                cleaned = best_sentence.replace('**', '').replace('\\', '')
                return cleaned.strip() + "."
            
            # If no good match found, return a generic response
            return "I couldn't find a specific answer to your question in the documentation."
            
        except Exception as e:
            logger.error(f"Error in direct response generation: {str(e)}")
            return "Could not generate a response due to an error." 
           
    @log_execution_time
    async def process_documentation_query(self, query: str) -> QueryResponse:
        """Process a query using the documentation"""
        total_start = time.time()
        try:
            # Find relevant documentation with timeout
            logger.info(f"Processing documentation query: {query}")
            
            # Run vector search in a separate thread with timeout
            loop = asyncio.get_event_loop()
            doc_search_start = time.time()
            relevant_docs = await asyncio.wait_for(
                loop.run_in_executor(self.executor, self._find_relevant_docs, query),
                timeout=20  # Increased timeout for document search
            )
            logger.info(f"Async document search took {time.time() - doc_search_start:.2f} seconds")
            
            if not relevant_docs:
                logger.warning("No relevant documentation found")
                return QueryResponse(
                    answer="I couldn't find any relevant documentation for your query.",
                    sources=[],
                    confidence_score=0.0,
                    used_internet_search=False
                )

            # Log retrieved document details
            doc = relevant_docs[0]  # Only use the most relevant doc
            logger.info(f"Retrieved document details:")
            logger.info(f"Title: {doc['title']}")
            logger.info(f"Path: {doc['path']}")
            logger.info(f"Content length: {len(doc['content'])} characters")
            logger.info(f"Content preview: {doc['content'][:200]}...")  # First 200 chars for preview

            # Create source with full content
            sources = [Source(
                title=doc['title'],
                content=doc['content'],  # Use full content
                relevance_score=1.0
            )]

            # Prepare context with full content
            context = f"Title: {doc['title']}\nContent: {doc['content']}"  # Use full content

            # Generate response using Ollama with timeout
            prompt = PROMPTS["documentation"].format(context=context, query=query)

            # Log the prompt being sent to the model
            logger.info(f"Sending prompt to model:")
            logger.info(f"System prompt: {prompt}")
            logger.info("User prompt:")
            logger.info("-" * 80)  # Separator for better readability
            logger.info(prompt)
            logger.info("-" * 80)  # Separator for better readability
            
            response_start = time.time()
            try:
                answer = await asyncio.wait_for(
                    loop.run_in_executor(self.executor, self._generate_response, prompt),
                    timeout=20  # Increased timeout for response generation
                )
                logger.info(f"Async response generation took {time.time() - response_start:.2f} seconds")
                
                # Log the generated answer
                logger.info(f"Generated answer: {answer}")
                
                logger.info(f"Total query processing took {time.time() - total_start:.2f} seconds")
                logger.info("Response generated successfully")
                return QueryResponse(
                    answer=answer,
                    sources=sources,
                    confidence_score=0.8,
                    used_internet_search=False
                )
            except asyncio.TimeoutError:
                logger.error("Documentation query processing timed out")
                # Try direct response as fallback
                try:
                    direct_answer = self._generate_direct_response(query, context)
                    return QueryResponse(
                        answer=direct_answer,
                        sources=sources,  # Use the same sources
                        confidence_score=0.5,
                        used_internet_search=False
                    )
                except Exception as e:
                    logger.error(f"Direct response generation failed: {str(e)}")
                    return QueryResponse(
                        answer="I'm having trouble processing your query. Please try again with a more specific question.",
                        sources=sources,  # Still include sources even for error case
                        confidence_score=0.0,
                        used_internet_search=False
                    )
        except Exception as e:
            logger.error(f"Error processing documentation query: {str(e)}", exc_info=True)
            return QueryResponse(
                answer="I encountered an error while processing your query. Please try again.",
                sources=[],
                confidence_score=0.0,
                used_internet_search=False
            )