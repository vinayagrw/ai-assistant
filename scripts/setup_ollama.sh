#!/bin/bash

echo "Starting Ollama server..."
ollama serve &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 5

echo "Pulling Mistral model..."
ollama pull mistral

echo "Setup complete! Ollama is ready to use."
echo "To stop the server, press Ctrl+C"

wait $SERVER_PID 