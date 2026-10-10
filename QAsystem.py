import os
import sqlite3
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings

load_dotenv()

conn = sqlite3.connect("db_history")
cursor= conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS db_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_name TEXT,
        question TEXT,
        answer TEXT
    )
"""
)
conn.commit()

def save_history(pdf_name, question, answer):
    cursor= conn.cursor()
    cursor.execute(
        "INSERT INTO db_history (pdf_name, question, answer) values(?,?,?)",
        (pdf_name, question, answer)
    )
    conn.commit()

embedding_model=SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt= ChatPromptTemplate.from_template(
    """
You are Zara, Abdul's AI assistant.
Answer the question based ONLY on the context below.
If the answer is not in the context, say 'This information is not in the document.'

Context:
{context}

Question: {question}
"""
)

def load_pdf(pdf_path):
    '''loads and split pdf'''
    print("!---Loading pdf---")
    loader=PyPDFLoader(pdf_path)
    document=loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks=splitter.split_documents(document)

    print(f"Split into {len(chunks)} chunks")
    return chunks

def build_vectordb(pdf_name, chunks):
    """Store chunks in ChromaDB."""
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=f"vectordb_{pdf_name}"
    )
    print("Stored in ChromaDB")
    return vectordb

def ask_question(vectordb, question, pdf_name):
    """Retrieve relevant chunks and ask Gemini."""
    relevent_chunks= vectordb.similarity_search(question, k=3)
    text=[ ]
    for chunk in relevent_chunks:
        text.append(chunk.page_content)

    chain=prompt | llm
    response = chain.invoke({
        "context": text,
       "question": question
    })
    answer = response.content
    save_history(pdf_name, question, answer)
    return answer

print("=== Zara Document Q&A System ===")
pdf_path = input("Enter PDF path: ").strip("'\"")
pdf_name = os.path.basename(pdf_path)

chunks = load_pdf(pdf_path)
vectordb = build_vectordb(pdf_name, chunks)

print(f"\nReady! Ask questions about {pdf_name}")
print("Type 'exit' to quit\n")

while True:
    question = input("Your question: ")
    if question.lower() == "exit":
        print("Goodbye!")
        break
    answer = ask_question(vectordb, question, pdf_name)
    print(f"Zara: {answer}\n")