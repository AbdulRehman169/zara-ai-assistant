import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
load_dotenv()
llm_genai = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)
store = {}
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
# InMemoryChatMessageHistory is used to store the chat history in memory for each session.
#  It allows you to keep track of the conversation context for a specific user session.
    return store[session_id]
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Zara, Abdul's helpful AI assistant."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])
chain = prompt | llm_genai
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
r1 = chain_with_memory.invoke(
    {"input": "My name is Abdul and I am from Karachi."},
    config={"configurable": {"session_id": "zara_session_1"}}
)
print("Zara:", r1.content)
print()
r2 = chain_with_memory.invoke(

    {"input": "Where am I from?"},

    config={"configurable": {"session_id": "zara_session_1"}}
)
print("Zara:", r2.content)