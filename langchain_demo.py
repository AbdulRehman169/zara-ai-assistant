from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import tavily as T
import os
import PIL.Image
import PyPDF2
from dotenv import load_dotenv

load_dotenv()
tavily_client=T.TavilyClient(os.getenv("TAVILY_API_KEY"))
llm_genai = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
llm_groq = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile")
@tool
def ask_genai(question: str) -> str:
    response=llm_genai.invoke(question)
    return response.content

@tool
def ask_groq(question: str) -> str:
    response=llm_groq.invoke(question)
    return response.content

@tool
def ask_with_image(question: str, image_path: str) -> str:
    image = PIL.Image.open(image_path)
    response = llm_genai.invoke([question, image])   
    return response.content

@tool

def ask_tavily(question: str) -> str:
    search_result = tavily_client.search(
        query= question,
        max_results=5
    )
    results = ""

    for result in search_result.get("result", []):
        results += (
            f"Title: {result['title']}\n"
            f"Content: {result['content']}\n\n"
        )

    return results
@tool
def ask_with_pdf(question: str, pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    response = llm_genai.invoke(f"Document: {text}\n\nQuestion: {question}")
    return response.content

tools=[
    ask_genai,
    ask_groq,
    ask_tavily,
    ask_with_image,
    ask_with_pdf
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Zara, a helpful AI assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm_genai, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)
result = agent_executor.invoke({
    "input": "What is weather today in faisalabad?"
})

print(result["output"])