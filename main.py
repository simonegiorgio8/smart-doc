from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from openai import embeddings
from openai.types import Upload
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import  RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_community.vectorstores import Pinecone
from pinecone_utils import get_vectorstore

from streamlit import context

# Carica la chiave API
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# inizializzo LangChain con OpenAI
memory= ConversationBufferMemory()
chat_model = ChatOpenAI(model="gpt-4", openai_api_key=openai_api_key)
conversation= ConversationChain(llm=chat_model, memory=memory)

vectorstore= get_vectorstore()

class ChatRequest(BaseModel):
    message: str

os.makedirs("./temp", exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vectorstore

    try:
        #salva temporaneamente il file
        file_path = f"./temp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        #carica il pdf e ne estrae il testo
        loader = PyPDFLoader(file_path)
        documents= loader.load()

        #divido il testo in blocchi per migliore elaborazione
        text_splitter= RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) #OpenAI consiglia di non superare i 8192 token per text-embedding-ada-002, ma è meglio restare tra 256 e 500 token per chunk
        chunks = text_splitter.split_documents(documents)

        #crea embeddings per la ricerca semantica
        embeddings= OpenAIEmbeddings( openai_api_key=openai_api_key)
        #vectorstore= FAISS.from_documents(chunks, embeddings)
        vectorstore= Pinecone.from_documents(chunks, embeddings, index_name=os.getenv("PINECONE_INDEX_NAME"))

        return {"message" : "File caricato con successo!", "filename": file.filename}
    except Exception as e:
        import traceback
        traceback.print_exc() #stampa l'errore in console
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def chat(request: ChatRequest):
    """Risponde alla domanda dell'utente basandosi sul contenuto del PDF caricato."""

    global vectorstore

    try:
        if vectorstore is not None:
            #se pdf caricato, cerca risposta in pinecone
            docs=vectorstore.similarity_search(request.message, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])

            messages = [
                SystemMessage(content="Sei un assistente esperto di manuali PDF. Rispondi basandoti sul seguente contenuto del documento."),
                HumanMessage(f"Documento:\n{context}\n\nDomanda:\n{request.message}"),
            ]

            response = chat_model.invoke(messages)

            memory.save_context({"input": request.message}, {"output": response.content})
            return {"reply": response.content}
        else:
            response= conversation.predict(input= request.message)
            return{"reply": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))