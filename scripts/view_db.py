import os
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from tabulate import tabulate

def view_database():
    """View and search ChromaDB data from command line"""
    # Check if vector_db exists
    vector_db_path = Path("vector_db")
    if not vector_db_path.exists():
        print(f"Vector database not found at {vector_db_path}")
        return

    # Initialize Chroma client
    client = chromadb.PersistentClient(
        path="vector_db",
        settings=Settings(allow_reset=True)
    )
    
    # Get all collections
    collections = client.list_collections()
    
    if not collections:
        print("No collections found in the database")
        return

    # Show collections
    print("\n=== Available Collections ===")
    for i, col in enumerate(collections, 1):
        print(f"{i}. {col.name}")

    # Get user selection
    while True:
        try:
            choice = int(input("\nSelect collection number (or 0 to exit): "))
            if choice == 0:
                return
            if 1 <= choice <= len(collections):
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")

    # Get selected collection
    collection = client.get_collection(collections[choice-1].name)
    
    # Show collection info
    print(f"\n=== Collection: {collection.name} ===")
    print(f"Total Documents: {collection.count()}")

    # Get all items
    results = collection.get()
    
    if not results['ids']:
        print("No documents found in collection")
        return

    # Show documents in a table
    print("\n=== Documents ===")
    table_data = []
    for i, (doc_id, doc, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas']), 1):
        # Truncate document content for display
        doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
        table_data.append([
            i,
            doc_id,
            doc_preview,
            json.dumps(metadata, indent=2)
        ])
    
    print(tabulate(
        table_data,
        headers=["#", "ID", "Content Preview", "Metadata"],
        tablefmt="grid"
    ))

    # Search interface
    while True:
        query = input("\nEnter search query (or 'q' to quit): ")
        if query.lower() == 'q':
            break
            
        if query:
            print("\n=== Search Results ===")
            search_results = collection.query(
                query_texts=[query],
                n_results=5
            )
            
            if search_results['ids'][0]:
                table_data = []
                for i, (doc_id, doc, metadata) in enumerate(zip(
                    search_results['ids'][0],
                    search_results['documents'][0],
                    search_results['metadatas'][0]
                ), 1):
                    # Truncate document content for display
                    doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
                    table_data.append([
                        i,
                        doc_id,
                        doc_preview,
                        json.dumps(metadata, indent=2)
                    ])
                
                print(tabulate(
                    table_data,
                    headers=["#", "ID", "Content Preview", "Metadata"],
                    tablefmt="grid"
                ))
            else:
                print("No results found")

if __name__ == "__main__":
    view_database() 