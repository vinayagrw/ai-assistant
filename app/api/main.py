from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
import time
import asyncio
import json
from flask_restx import Api, fields, Resource, Namespace, reqparse

# Load environment variables from .env file
load_dotenv()

from app.core.ai_assistant import AIAssistant
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.utils.logger import logger, log_execution_time
from app.config.model_config import MODEL_PRIORITY, MODEL_PARAMS, OLLAMA_CONFIG


app = Flask(__name__)
api = Api(app, version='1.0', title='AI Assistant API Documentation',description='AI Assistant API Documentation')
my_namespace = Namespace('', description='AI Assistant')
api.add_namespace(my_namespace)

def init_assistant():
    """Initialize the AI Assistant"""
    global assistant
    try:
        logger.info(f"Initializing AI Assistant...")
        assistant = AIAssistant()
        logger.info("AI Assistant initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing AI Assistant: {str(e)}")
        logger.error(f"Current OPENAI_API_KEY value: ")
        raise

# Initialize assistant at startup
init_assistant()

def log_response(request_id: str, response: QueryResponse, processing_time: float):
    """Log API response with details"""
    try:

        log_entry = {
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_time": f"{processing_time:.2f}s",
            "response": {
                "answer": response.answer,
                "confidence_score": response.confidence_score,
                "used_internet_search": response.used_internet_search,
                "sources_count": len(response.sources)
            }
        }
        

        logger.info(f"API Response: {json.dumps(log_entry, indent=2)}")

        if response.sources:
            logger.info("Response Sources:")
            for idx, source in enumerate(response.sources, 1):
                logger.info(f"Source {idx}:")
                logger.info(f"  Title: {source.title}")
                logger.info(f"  URL: {source.url}")
                logger.info(f"  Relevance Score: {source.relevance_score}")
                logger.info(f"  Content Preview: {source.content[:200]}...")
    except Exception as e:
        logger.error(f"Error logging response: {str(e)}")

query_parser = reqparse.RequestParser()
query_parser.add_argument('query', type=str, required=True, help='Query string')

query_model = my_namespace.model('QueryModel', {
    'query': fields.String(required=True, description='The query string to process', example='What is DuploCloud?')
})

@my_namespace.route('/query')
class QueryResource(Resource):
    @api.expect(query_model)
    @api.doc(description="Process a user query and return a response with sources.")
    def post(self):
        """Process a user query"""
        return asyncio.run(self._handle_request())

    async def _handle_request(self):
        try:
            start_time = time.time()

            data = request.get_json()
            query = data.get('query', '')

            request_id = request.headers.get("X-Request-ID", str(time.time()))
            logger.info(f"Processing request {request_id}:")
            logger.info(f"Query: {query}")

            response = await assistant.process_query(query)
            processing_time = time.time() - start_time
            log_response(request_id, response, processing_time)
            return jsonify(response.dict())

        except Exception as e:
            error_detail = f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
            logger.error(error_detail)
            response = QueryResponse(
                answer=f"An error occurred: {str(e)}. Please try again.",
                sources=[],
                confidence_score=0.0,
                used_internet_search=False
            )
            return jsonify(response.dict())


@my_namespace.route('/health')
class QueryResource(Resource):
    @api.doc()
    def get(self):
        """Health check endpoint"""
        try:
            response = {
                "status": "healthy",
            }
            logger.info(f"Health Check Response: {json.dumps(response, indent=2)}")
            return jsonify(response)  # Ensure a valid response is returned
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            response = {
                "status": "unhealthy",
                "error": str(e)
            }
            logger.error(f"Health Check Error Response: {json.dumps(response, indent=2)}")
            return jsonify(response), 500  # Return a valid error response
