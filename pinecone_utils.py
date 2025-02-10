import os
import pinecone
from dotenv import load_dotenv
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from pinecone import ServerlessSpec  # Import necessario

# Carica le variabili d'ambiente
load_dotenv()

# Inizializza il client Pinecone
pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Nome dell'indice
index_name = os.getenv("PINECONE_INDEX_NAME")

# Controlla se l'indice esiste, altrimenti lo crea
existing_indexes = [index["name"] for index in pc.list_indexes()]

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=1536,  # dimendione degli embedding creati con OpenAI text-embedding-ada-002
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Specifica il cloud e la regione
    )

# Connetti all'indice
index = pc.Index(index_name)

# Funzione per ottenere il vectorstore da Pinecone
def get_vectorstore():
    return Pinecone.from_existing_index(index_name, OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY")))
