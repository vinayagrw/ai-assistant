"""Model configuration settings"""

# Model priority for different types of queries
MODEL_PRIORITY = [
    "phi"#,          # Fastest model first
    # "mistral",      # Good balance of speed and quality
    # "neural-chat"   # Most capable but slowest
]

# Model-specific parameters
MODEL_PARAMS = {
    "phi": {
        "temperature": 0.1,    # Very low temperature for factual responses
        "top_p": 0.5,         # Very focused responses
        "top_k": 10,          # Very narrow range
        "repeat_penalty": 1.1, # Prevent repetition
        "timeout": 5,         # Shorter timeout for faster fallback
        "num_predict": 50,    # Shorter responses for speed
        "retry_on_error": True, # Retry on error
        "max_retries": 1,     # Only retry once
        "concurrent_requests": 3  # Allow 3 concurrent requests
    },
    "mistral": {
        "temperature": 0.3,    # Low temperature for accuracy
        "top_p": 0.6,         # Focused responses
        "top_k": 20,          # Narrow range
        "repeat_penalty": 1.1, # Prevent repetition
        "timeout": 8,         # Shorter timeout
        "num_predict": 100,   # Moderate response length
        "retry_on_error": True, # Retry on error
        "max_retries": 1,     # Only retry once
        "concurrent_requests": 2  # Allow 2 concurrent requests
    },
    "neural-chat": {
        "temperature": 0.2,    # Low temperature for precision
        "top_p": 0.6,         # Focused token selection
        "top_k": 15,          # Narrow range for precise answers
        "repeat_penalty": 1.1, # Prevent repetition
        "timeout": 10,        # Shorter timeout
        "num_predict": 150,   # Longer responses for detailed answers
        "retry_on_error": True, # Retry on error
        "max_retries": 1,     # Only retry once
        "concurrent_requests": 1  # Allow 1 concurrent request
    }
}

# Ollama configuration
OLLAMA_CONFIG = {
    "base_url": "http://127.0.0.1:11434",
    "timeout": 15,  # Shorter overall timeout
    "max_retries": 1,  # Only retry once
    "retry_delay": 0.5,  # Shorter delay between retries
    "error_handling": {
        "retry_on_timeout": False,  # Don't retry on timeout
        "retry_on_error": True,     # Retry on other errors
        "fallback_on_error": True,  # Fallback to next model
        "log_errors": True,         # Log errors
        "timeout_strategy": "fast_fail",  # Fail fast on timeout
        "concurrent_handling": {
            "enabled": True,
            "max_concurrent": 3,     # Maximum concurrent requests
            "queue_size": 10,        # Maximum queue size
            "queue_timeout": 5,      # Queue timeout in seconds
            "reject_on_full": True   # Reject new requests when queue is full
        }
    }
}

# Vector database configuration
VECTOR_DB_CONFIG = {
    "path": "vector_db",
    "collection_name": "documentation",
    "similarity_threshold": 0.45,  # Much lower threshold for better recall
    "duplo_similarity_threshold": 0.35,  # Much lower threshold for Duplo-specific content
    "hnsw_config": {  # HNSW index configuration for small datasets
        "M": 16,      # Lower M for better accuracy in small datasets
        "ef_construction": 100,  # Higher construction accuracy
        "ef_search": 50,        # Higher search accuracy
        "max_elements": 1000    # Expected max elements
    },
    "error_handling": {
        "retry_on_error": True,
        "fallback_to_keyword": True,
        "cache_results": True
    }
}

# DuploCloud keywords for fallback matching
DUPLO_KEYWORDS = [
    "duplo", "duplocloud", "infrastructure", "deployment", "cloud",
    "application focused", "application interface", "vpc", "vnet",
    "kubernetes", "k8s", "ecs", "tenant", "plan", "diagnostics",
    "app service", "cloud service", "devsecops"
]

# Response handling configuration
RESPONSE_CONFIG = {
    "min_confidence": 0.3,     # Even lower confidence threshold
    "max_sources": 2,         # Fewer sources but more relevant
    "min_sources": 1,         # Require at least one source
    "fallback_message": "I couldn't find a specific answer to your question in the documentation. Would you like me to search for related information or try a different approach?",
    "error_handling": {
        "retry_on_error": False,  # Don't retry on error
        "fallback_to_simple": True,
        "log_errors": True,
        "error_message": "I encountered an issue while processing your query. Let me try a different approach.",
        "timeout_handling": {
            "enabled": True,
            "max_attempts": 1,     # Only try once
            "fallback_message": "I'm taking too long to respond. Please try again with a simpler query.",
            "fast_fail": True,     # Fail fast on timeout
            "concurrent_handling": {
                "enabled": True,
                "max_concurrent": 3,     # Maximum concurrent requests
                "queue_size": 10,        # Maximum queue size
                "queue_timeout": 5,      # Queue timeout in seconds
                "reject_on_full": True,  # Reject new requests when queue is full
                "reject_message": "The server is currently busy. Please try again in a few seconds."
            }
        }
    },
    "answer_extraction": {
        "enabled": True,
        "min_sentence_length": 10,
        "max_sentence_length": 200,
        "boost_exact_matches": True,
        "boost_header_matches": True,
        "boost_key_terms": True,
        "clean_response": True,  # Clean up response formatting
        "remove_metadata": True,  # Remove metadata from response
        "format_options": {
            "remove_title": True,
            "remove_urls": True,
            "remove_markdown": True,
            "remove_html": True,
            "remove_images": True,
            "remove_figures": True,
            "remove_captions": True,
            "clean_whitespace": True,
            "normalize_quotes": True,
            "normalize_dashes": True,
            "remove_metadata_prefix": True,  # Remove "Title:" and similar prefixes
            "remove_content_prefix": True,   # Remove "Content:" prefix
            "remove_header_markers": True,   # Remove "#" and similar markers
            "clean_newlines": True,          # Clean up newlines
            "join_sentences": True,          # Join related sentences
            "remove_extra_spaces": True,     # Remove multiple spaces
            "remove_all_prefixes": True,     # Remove all known prefixes
            "remove_all_markers": True,      # Remove all known markers
            "strip_metadata": True,          # Strip all metadata
            "clean_formatting": True,        # Clean all formatting
            "remove_json_wrapper": True,     # Remove JSON wrapper
            "remove_source_info": True,      # Remove source information
            "remove_confidence": True,       # Remove confidence score
            "remove_search_info": True       # Remove search information
        },
        "response_format": {
            "type": "plain_text",           # Output as plain text
            "include_sources": False,        # Don't include sources in response
            "include_confidence": False,     # Don't include confidence score
            "include_metadata": False,       # Don't include any metadata
            "trim_response": True,          # Trim response to essential content
            "capitalize_first": True,       # Capitalize first letter
            "end_with_period": True,        # End with period if not present
            "clean_output": True,           # Clean the final output
            "remove_prefixes": True,        # Remove any remaining prefixes
            "remove_markers": True,         # Remove any remaining markers
            "strip_metadata": True,         # Strip any remaining metadata
            "format_rules": [
                {"pattern": r"^Title:.*?\n", "replacement": ""},
                {"pattern": r"^Content:.*?\n", "replacement": ""},
                {"pattern": r"^#\s*", "replacement": ""},
                {"pattern": r"\n+", "replacement": " "},
                {"pattern": r"\s+", "replacement": " "},
                {"pattern": r"^\s+|\s+$", "replacement": ""},
                {"pattern": r"^.*?Content:\s*", "replacement": ""},
                {"pattern": r"^.*?Title:\s*", "replacement": ""},
                {"pattern": r"^.*?#\s*", "replacement": ""},
                {"pattern": r"^.*?Application Focused Interface\s*", "replacement": ""}
            ]
        },
        "post_processing": {
            "enabled": True,
            "remove_metadata": True,
            "clean_formatting": True,
            "normalize_text": True,
            "rules": [
                {"type": "regex", "pattern": r"^Title:.*?\n", "replacement": ""},
                {"type": "regex", "pattern": r"^Content:.*?\n", "replacement": ""},
                {"type": "regex", "pattern": r"^#\s*", "replacement": ""},
                {"type": "regex", "pattern": r"\n+", "replacement": " "},
                {"type": "regex", "pattern": r"\s+", "replacement": " "},
                {"type": "regex", "pattern": r"^\s+|\s+$", "replacement": ""},
                {"type": "string", "find": "Title:", "replace": ""},
                {"type": "string", "find": "Content:", "replace": ""},
                {"type": "string", "find": "#", "replace": ""},
                {"type": "string", "find": "Application Focused Interface", "replace": ""},
                {"type": "string", "find": "Title: README Content:", "replace": ""},
                {"type": "string", "find": "Title: README", "replace": ""},
                {"type": "string", "find": "Content: #", "replace": ""}
            ]
        }
    }
}

# Optimized chunking for small datasets
CHUNKING_CONFIG = {
    # Semantic chunking - optimized for small datasets
    "semantic": {
        "enabled": True,
        "min_chunk_size": 30,     # Even smaller chunks for more granular matching
        "max_chunk_size": 200,    # Smaller max size for better precision
        "overlap": 20,            # More overlap for better context
        "split_on": [             # Prioritize natural breaks
            "\n\n",              # Paragraphs
            ". ",                # Sentences
            "! ",                # Exclamations
            "? ",                # Questions
            "; ",                # Semicolons
            ": ",                # Colons
            ", ",                # Commas
            " "                  # Words
        ],
        "clean_chunks": True,    # Clean chunks during splitting
        "remove_metadata": True,  # Remove metadata from chunks
        "error_handling": {
            "retry_on_error": True,
            "fallback_to_simple": True
        }
    },
    
    # Structural chunking - preserve document structure
    "structural": {
        "enabled": True,
        "markdown_headers": True,  # Split on headers
        "code_blocks": True,      # Keep code together
        "lists": True,           # Keep lists together
        "tables": True,          # Keep tables together
        "preserve_hierarchy": True, # Keep header hierarchy
        "preserve_metadata": False,  # Don't preserve metadata
        "error_handling": {
            "retry_on_error": True,
            "fallback_to_simple": True
        }
    },
    
    # Context-aware chunking - maximize context
    "context": {
        "enabled": True,
        "preserve_headers": False,  # Don't include headers in response
        "include_metadata": False,  # Don't include metadata
        "context_window": 4,       # Even larger context window
        "include_siblings": True,  # Include sibling chunks
        "include_parents": True,   # Include parent chunks
        "error_handling": {
            "retry_on_error": True,
            "fallback_to_simple": True
        }
    },
    
    # Query-specific chunking - optimize for relevance
    "query_aware": {
        "enabled": True,
        "min_relevance": 0.2,     # Even lower relevance threshold
        "max_chunks": 3,         # Fewer but more relevant chunks
        "chunk_combine": True,    # Combine related chunks
        "boost_headers": True,    # Boost header matches
        "boost_exact": True,      # Boost exact matches
        "boost_keywords": True,   # Boost keyword matches
        "error_handling": {
            "retry_on_error": True,
            "fallback_to_simple": True
        }
    }
}

# Embedding configuration for small datasets
EMBEDDING_CONFIG = {
    "model": "all-MiniLM-L6-v2",  # Good balance of speed and quality
    "dimension": 384,             # Standard dimension
    "normalize": True,            # Normalize vectors
    "pooling": "mean",            # Mean pooling for better semantic understanding
    "preprocessing": {
        "lowercase": True,        # Convert to lowercase
        "remove_punctuation": True, # Remove punctuation
        "remove_stopwords": False,  # Keep stopwords for context
        "lemmatize": True,        # Lemmatize words
        "preserve_numbers": True,  # Keep numbers
        "preserve_special_chars": True,  # Keep special characters
        "remove_metadata": True,   # Remove metadata during preprocessing
        "clean_formatting": True   # Clean formatting during preprocessing
    },
    "error_handling": {
        "retry_on_error": True,
        "fallback_to_simple": True,
        "cache_embeddings": True
    }
} 