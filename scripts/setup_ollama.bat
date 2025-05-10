@echo off
echo Starting Ollama server...
start /B ollama serve

echo Waiting for server to start...
timeout /t 5 /nobreak

echo Pulling Mistral model...
ollama pull mistral

echo Setup complete! Ollama is ready to use.
echo To stop the server, press Ctrl+C 