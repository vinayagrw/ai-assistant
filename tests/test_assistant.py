import pytest
import logging

from app.core.ai_assistant import AIAssistant
from app.models.schemas import QueryResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def assistant():
    """Create an AI Assistant instance for testing"""
    return AIAssistant()

@pytest.mark.asyncio
async def test_process_query(assistant):
    """Test the query processing functionality"""
    # Test with a simple query
    queries = [
        "What is DuploCloud?",
        "what is capital of the USA"
    ]
    
    for query in queries:
        logger.info(f"Processing query: {query}")
        response = await assistant.process_query(query)
        logger.info(f"Response for query '{query}': {response}")

        assert isinstance(response, QueryResponse)
        assert isinstance(response.answer, str)
        assert isinstance(response.sources, list)
        assert isinstance(response.confidence_score, float)
        assert isinstance(response.used_internet_search, bool)
        
        # Verify response content
        assert len(response.answer) > 0
        assert 0 <= response.confidence_score <= 1 