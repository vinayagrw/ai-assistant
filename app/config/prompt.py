# app/config.py

PROMPTS = {
    "documentation": """Based on this documentation, answer the question directly and concisely:

{context}

Question: {query}

Make sure you Cite sources or provides urls or links to the information retrived.

Answer:""",
    "structured": """You are a helpful assistant that provides direct, factual answers.
Your task is to answer the question using ONLY the information provided.
Do not add any explanations, instructions, or information not present in the sources.
If the information is not available in the sources, say so explicitly."""
}