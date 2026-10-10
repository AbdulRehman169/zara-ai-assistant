import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain_groq import ChatGroq
import tavily as ti
load_dotenv()
# Block 1: the AI model (same as Day 1)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

# Block 2: a reusable prompt TEMPLATE with a blank spot to fill in
prompt = ChatPromptTemplate.from_template("You are Zara, Abdul's assistant. Answer this: {question}")

# Block 3: cleans up the output so you get plain text back, not a whole response object
output_parser = StrOutputParser()

# Now CHAIN them together with the pipe symbol
chain = prompt | llm | output_parser

# Run the whole chain in one call
answer = chain.invoke({"question": "What is Python in one sentence?"})
print(answer)

tavily_client=ti.TavilyClient(os.getenv("TAVILY_API_KEY"))
@tool
def search_web(question: str) -> str:
    """Searches the internet for current, up-to-date information.
    Use this when the user asks about recent events, current prices,
    today's weather, or anything that changes over time."""
    search_result = tavily_client.search(query=question, max_results=5)
    web_results = ""
    for result in search_result.get("results", []):
        web_results += f"Title: {result['title']}\nContent: {result['content'][:200]}\n\n"
    return web_results
Groq_client = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")   # ✅
@tool
def ask_groq(question: str) -> str:
    response = Groq_client.invoke(question)
    return response.content
