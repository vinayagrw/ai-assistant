from app.config.model_config import VECTOR_DB_CONFIG, DUPLO_KEYWORDS

import logging

logger = logging.getLogger(__name__)

class DuploRelated:
    def __init__(self, collection):
        self.collection = collection

    def is_duplo_related(self, query: str) -> bool:
        """Check if the query is related to DuploCloud using vector similarity"""
        try:
            # Search vector database for similar content
            results = self.collection.query(
                query_texts=[query],
                n_results=1
            )
            
            # If we have results and the distance is below threshold, consider it related
            if results['distances'][0]:
                distance = results['distances'][0][0]
                is_related = distance < VECTOR_DB_CONFIG["duplo_similarity_threshold"]
                logger.debug(f"Query '{query}' similarity distance: {distance}, is DuploCloud related: {is_related}")
                return is_related
            
            return False

        except Exception as e:
            logger.error(f"Error in vector similarity check: {str(e)}")
            query_clean = ''.join(c.lower() for c in query if c.isalnum() or c.isspace())
            return any(keyword.lower() in query_clean for keyword in DUPLO_KEYWORDS)