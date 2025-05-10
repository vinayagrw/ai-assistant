import streamlit as st
import chromadb
from chromadb.config import Settings
import pandas as pd
import numpy as np
from pathlib import Path

def init_chroma_client():
    """Initialize ChromaDB client"""
    vector_db_path = Path("vector_db")
    if not vector_db_path.exists():
        st.error(f"Vector database not found at {vector_db_path}")
        return None
    
    return chromadb.PersistentClient(
        path=str(vector_db_path),
        settings=Settings(allow_reset=True)
    )

def display_collection_info(collection):
    """Display collection information"""
    st.header("Collection Information")
    st.write(f"Name: {collection.name}")
    st.write(f"Total Documents: {collection.count()}")

def display_documents_table(collection):
    """Display documents in a table format"""
    st.header("Documents")
    
    # Get all items with embeddings
    results = collection.get(include=['documents', 'metadatas', 'embeddings'])
    
    if not results['ids']:
        st.write("No documents found in collection")
        return
    
    # Create DataFrame for documents
    df = pd.DataFrame({
        'ID': results['ids'],
        'Document': results['documents'],
        'Metadata': [str(m) for m in results['metadatas']]
    })
    
    # Add embedding information if available
    if results.get('embeddings'):
        df['Embedding'] = [f"Vector[{len(emb)}]" for emb in results['embeddings']]
        df['Embedding Stats'] = [
            f"Mean: {np.mean(emb):.4f}, Std: {np.std(emb):.4f}"
            for emb in results['embeddings']
        ]
    
    # Display the table
    st.dataframe(
        df,
        use_container_width=True,
        height=400
    )
    
    # Download button for the data
    csv = df.to_csv(index=False)
    st.download_button(
        "Download Data",
        csv,
        "chroma_data.csv",
        "text/csv",
        key='download-csv'
    )

def display_search_results(collection, query):
    """Display search results"""
    st.header("Search Results")
    
    search_results = collection.query(
        query_texts=[query],
        n_results=5,
        include=['documents', 'metadatas', 'distances', 'embeddings']
    )
    
    if not search_results['ids'][0]:
        st.write("No results found")
        return
    
    # Create DataFrame for search results
    search_df = pd.DataFrame({
        'ID': search_results['ids'][0],
        'Document': search_results['documents'][0],
        'Metadata': [str(m) for m in search_results['metadatas'][0]],
        'Distance': [f"{d:.4f}" for d in search_results['distances'][0]]
    })
    
    # Add embedding information if available
    if search_results.get('embeddings') and search_results['embeddings'][0]:
        search_df['Embedding'] = [f"Vector[{len(emb)}]" for emb in search_results['embeddings'][0]]
        search_df['Embedding Stats'] = [
            f"Mean: {np.mean(emb):.4f}, Std: {np.std(emb):.4f}"
            for emb in search_results['embeddings'][0]
        ]
    
    st.dataframe(
        search_df,
        use_container_width=True,
        height=300
    )
    
    # Download button for search results
    search_csv = search_df.to_csv(index=False)
    st.download_button(
        "Download Search Results",
        search_csv,
        "search_results.csv",
        "text/csv",
        key='download-search-csv'
    )

def main():
    st.set_page_config(page_title="ChromaDB Admin", layout="wide")
    st.title("ChromaDB Admin Interface")
    
    # Initialize client
    client = init_chroma_client()
    if not client:
        return
    
    # Get all collections
    collections = client.list_collections()
    if not collections:
        st.warning("No collections found in the database")
        return
    
    # Collection selector
    selected_collection = st.selectbox(
        "Select Collection",
        [col.name for col in collections]
    )
    
    if selected_collection:
        collection = client.get_collection(selected_collection)
        
        # Display collection info
        display_collection_info(collection)
        
        # Display documents
        display_documents_table(collection)
        
        # Search interface
        st.header("Search")
        query = st.text_input("Enter search query")
        if query:
            display_search_results(collection, query)

if __name__ == "__main__":
    main() 