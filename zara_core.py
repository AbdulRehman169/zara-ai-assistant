import os
import PIL.Image
import pyodbc
import PyPDF2
import tavily as Tavily
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
load_dotenv()
DB_server = os.getenv("DB_SERVER")
Groq_API_KEY = os.getenv("GROQ_API_KEY")
Gemini_API_KEY = os.getenv("GEMINI_API_KEY")
Tavily_API_KEY = os.getenv("TAVILY_API_KEY")

if not all([DB_server, Groq_API_KEY, Gemini_API_KEY, Tavily_API_KEY]):
    print("One or more required environment variables are missing.")
    raise SystemExit(
        "Please set DB_SERVER, GROQ_API_KEY, GEMINI_API_KEY, and TAVILY_API_KEY in your environment."
    )

tavily = Tavily.TavilyClient(api_key=Tavily_API_KEY)
llm_groq = ChatGroq(api_key=Groq_API_KEY, model="llama-3.3-70b-versatile")
llm_gemini = ChatGoogleGenerativeAI(
    api_key=Gemini_API_KEY, model="gemini-2.5-flash"
)

# SQL Connection Setup
try:
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_server};"
        "DATABASE=AI_History;"
        "Trusted_Connection=yes"
    )
except Exception as e:
    print(f"⚠️ Could not connect to SQL Server: {e}")
    print("Zara will continue, but chat history won't be saved to DB.")
    conn = None


def save_history(question, answer):
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (Chat) VALUES (?)",
                (question + " - " + answer,),
            )
            conn.commit()
        except Exception as e:
            print(f"⚠️ Could not save chat history: {e}")


# Define Agent Tools
@tool
def ask_groq(question: str) -> str:
    """Answers general questions using Groq's fast LLaMA model.
    Use this for quick factual questions that don't need
    web search, image analysis, or PDF reading."""
    response = llm_groq.invoke(question)
    return response.content


@tool
def search_web(question: str) -> str:
    """Searches the internet for current, up-to-date information.
    Use this when the user asks about recent events, current prices,
    today's weather, or anything that changes over time."""
    search_result = tavily.search(query=question, max_results=5)
    web_results = ""
    for result in search_result.get("results", []):
        web_results += (
            f"Title: {result['title']}\nContent: {result['content'][:200]}\n\n"
        )
    return web_results


@tool
def ask_with_image(question: str, image_path: str) -> str:
    """Analyzes an uploaded image and answers a question about it.
    Use this when the user has provided an image file path and wants
    to know what's in it or asks a question about a picture."""
    image = PIL.Image.open(image_path)
    response = llm_gemini.invoke([question, image])
    return response.content


@tool
def ask_about_pdf(question: str, pdf_path: str) -> str:
    """Reads a PDF file and answers a question based on its content.
    Use this when the user has provided a PDF file path and wants
    a summary, key points, or a specific answer from the document."""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    response = llm_gemini.invoke(f"Document: {text}\n\nQuestion: {question}")
    return response.content


tools = [ask_groq, search_web, ask_with_image, ask_about_pdf]

# System prompt string
system_prompt = (
    "You are Zara, Abdul's personal AI assistant. "
    "You are helpful, friendly, and concise. "
    "Always respond in the same language the user writes in."
)

system_prompt=system_prompt,

# Initialize short-term memory checkpointer
memory = InMemorySaver()

# Build the LangGraph React Agent graph
agent_executor = create_agent(
    model=llm_gemini,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=memory,
)


def ask_zara(question: str, session_id="default_session") -> str:

    config = {"configurable": {"thread_id": session_id}}

    user_input = {"messages": [HumanMessage(content=question)]}

    result = agent_executor.invoke(user_input, config=config)
    all_messages = result["messages"]
    last_message = all_messages[-1]
    answer = last_message.content
    save_history(question, answer)
    return answer


def view_history():
    """Returns all rows from SQL history table."""
    if conn is None:
        print("⚠️ No database connection. Cannot view history.")
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history")
    rows = cursor.fetchall()
    cursor.close()
    return rows


def start_new_conversation(session_id="default_session"):
    """Resets memory for a given session in LangGraph memory."""
    memory.delete_thread(session_id)