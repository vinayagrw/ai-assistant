import os
import chromadb
from chromadb.config import Settings
import pandas as pd
from tabulate import tabulate
import json
from pathlib import Path

def visualize_vector_db():
    """Visualize the contents of the Chroma vector database"""
    # Initialize Chroma client
    vector_db_path = "vector_db"
    if not os.path.exists(vector_db_path):
        print(f"Vector database not found at {vector_db_path}")
        return

    client = chromadb.PersistentClient(
        path=vector_db_path,
        settings=Settings(allow_reset=True)
    )
    
    # Get the collection
    collection = client.get_collection("documentation")
    
    # Get all items from the collection
    results = collection.get()
    
    if not results['ids']:
        print("No documents found in the vector database")
        return
    
    # Create a list of dictionaries for each document chunk
    documents = []
    for i in range(len(results['ids'])):
        doc = {
            'id': results['ids'][i],
            'document': results['documents'][i],
            'metadata': results['metadatas'][i]
        }
        documents.append(doc)
    
    # Convert to DataFrame for better visualization
    df = pd.DataFrame(documents)
    
    # Print summary statistics
    print("\n=== Vector Database Summary ===")
    print(f"Total chunks: {len(documents)}")
    print(f"Unique documents: {len(set(doc['metadata']['title'] for doc in documents))}")
    
    # Print document titles and their chunk counts
    print("\n=== Document Chunk Distribution ===")
    title_counts = df['metadata'].apply(lambda x: x['title']).value_counts()
    print(tabulate(
        [[title, count] for title, count in title_counts.items()],
        headers=['Document Title', 'Number of Chunks'],
        tablefmt='grid'
    ))
    
    # Print sample chunks
    print("\n=== Sample Document Chunks ===")
    for i, doc in enumerate(documents[:3]):  # Show first 3 chunks
        print(f"\nChunk {i+1}:")
        print(f"ID: {doc['id']}")
        print(f"Title: {doc['metadata']['title']}")
        print(f"Path: {doc['metadata']['path']}")
        print(f"Chunk Index: {doc['metadata']['chunk_index']}")
        print(f"Content Preview: {doc['document'][:200]}...")
    
    # Save detailed data to JSON file
    output_file = "vector_db_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2)
    print(f"\nDetailed data saved to {output_file}")

if __name__ == "__main__":
    visualize_vector_db() 