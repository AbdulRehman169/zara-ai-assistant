import sqlite3
import os
from dotenv import load_dotenv
from langchain_community.agents import agents
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

conn= sqlite3.connect("qa_history.db")

cursor= conn.cursor()

cursor.execute(
    '''
    create table if not exist qa_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
       pdf_name TEXT,
       question TEXT,
       answer TEXT
    )'''
)
conn.commit()

