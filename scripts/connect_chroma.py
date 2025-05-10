import chromadb
from chromadb.config import Settings
from pathlib import Path
import json

class ChromaConnector:
    def __init__(self, db_path="vector_db"):
        """Initialize connection to ChromaDB"""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"Creating database at {self.db_path}")
            self.db_path.mkdir(parents=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(allow_reset=True)
        )
        print(f"Connected to ChromaDB at {self.db_path}")

    def list_collections(self):
        """List all collections in the database"""
        collections = self.client.list_collections()
        if not collections:
            print("No collections found")
            return []
        
        print("\nAvailable Collections:")
        for i, col in enumerate(collections, 1):
            print(f"{i}. {col.name} ({col.count()} documents)")
        return collections

    def get_collection(self, collection_name):
        """Get a specific collection"""
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            print(f"Error getting collection: {e}")
            return None

    def create_collection(self, name):
        """Create a new collection"""
        try:
            return self.client.create_collection(name)
        except Exception as e:
            print(f"Error creating collection: {e}")
            return None

    def add_documents(self, collection_name, documents, metadatas=None, ids=None):
        """Add documents to a collection"""
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                print(f"Collection {collection_name} not found")
                return False
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    def search(self, collection_name, query, n_results=5):
        """Search documents in a collection"""
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                print(f"Collection {collection_name} not found")
                return None
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return None

def main():
    # Example usage
    connector = ChromaConnector()
    
    # List collections
    collections = connector.list_collections()
    
    if collections:
        # Example: Get first collection
        collection = collections[0]
        print(f"\nCollection info: {collection.name}")
        print(f"Document count: {collection.count()}")
        
        # Example: Search
        query = input("\nEnter search query (or press Enter to skip): ")
        if query:
            results = connector.search(collection.name, query)
            if results:
                print("\nSearch Results:")
                for i, (doc_id, doc, metadata) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0]
                ), 1):
                    print(f"\nResult {i}:")
                    print(f"ID: {doc_id}")
                    print(f"Content: {doc[:200]}...")
                    print(f"Metadata: {json.dumps(metadata, indent=2)}")

if __name__ == "__main__":
    main() 