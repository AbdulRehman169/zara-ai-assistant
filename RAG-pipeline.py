import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import sqlite3

conn = sqlite3.connect("rag_history.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS rag_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        context_used TEXT,
        answer TEXT
    )
""")
conn.commit()

def save_rag_history(question, context, answer):
    cursor.execute(
        "INSERT INTO rag_history (question, context_used, answer) VALUES (?, ?, ?)",
        (question, context, answer)
    )
    conn.commit()

def view_rag_history():
    cursor.execute("SELECT * FROM rag_history")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]} | Q: {row[1]} | A: {row[3]}")#row[2] is context, row[3] is answer, row[0] is id, row[1] is question

load_dotenv()

loader = TextLoader("sample.txt")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)
chunks = splitter.split_documents(documents)
print(f"Loaded and split into {len(chunks)} chunks")

embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory="rag_vectordb"
)
print("Stored in ChromaDB")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt = ChatPromptTemplate.from_template("""
You are Zara, Abdul's AI assistant.
Answer the question based ONLY on the context below.
If the answer is not in the context, say 'I don't have that information.'

Context:
{context}

Question: {question}
""")

def ask_rag(question):
    matching_documents = vectordb.similarity_search(question, k=2)
    text_pieces = []
    for chunk in matching_documents:
        text_pieces.append(chunk.page_content)
        
    full_context = "\n".join(text_pieces)
    ai_inputs = {
        "context": full_context,
        "question": question
    }
    
    ai_pipeline = prompt | llm
    
    ai_response = ai_pipeline.invoke(ai_inputs)
    
    print("----------------------------------------")
    print("QUESTION ASKED:", question)
    print("CONTEXT FOUND:", full_context)
    print("AI ANSWER:", ai_response.content)
    print("----------------------------------------")

    save_rag_history(question, full_context, ai_response.content)
    
    return ai_response.content

ask_rag("What AI models does Zara support?")
ask_rag("Where is Abdul from?")
ask_rag("What is the capital of France?")