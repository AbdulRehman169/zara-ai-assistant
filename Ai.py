import pyodbc
import groq as gr
import google.generativeai as genai
import prompt_library as pl
import PIL.Image
import PyPDF2
import tavily as T
import os
from dotenv import load_dotenv
from flask import Flask
print("=" * 55)
print("Welcome to ZARA — Abdul's AI Assistant💕🤖✨")
print("=" * 55)
print()
load_dotenv()
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
DB_server=os.getenv("DB_SERVER")
if not all([TAVILY_API_KEY, GROQ_API_KEY, GEMINI_API_KEY]):
    print("⚠️☠️  One or more API keys are missing.")
    print("    Create a .env file (see .env.example) with:")
    print("    GEMINI_API_KEY=...  GROQ_API_KEY=...  TAVILY_API_KEY=...")
    raise SystemExit(1)

tavily_client = T.TavilyClient(api_key=TAVILY_API_KEY)   
groq_client = gr.Client(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY) 

try:
    conn=pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={DB_server};'
        'DATABASE=AI_History;'
        'Trusted_Connection=yes'
)
except Exception as e:
    print(f"⚠️Could not connect to SQL Server: {e}")
    print("    Zara will continue, but chat history won't be saved.")
    conn = None
def read_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            total_pages = len(reader.pages)
            print(f"PDF loaded: {total_pages} pages found.")
            for page in reader.pages:
                text += page.extract_text()
        return text
    except FileNotFoundError:
        return "PDF file not found. Please check the path."
    except Exception as e:
        return f"Error reading PDF: {e}"
def ask_about_pdf(question, pdf_path):
    print("Reading PDF...")
    pdf_text = read_pdf(pdf_path)
    if "Error" in pdf_text or "not found" in pdf_text:
        return pdf_text
    print("Sending to Zara...")
    response = model.generate_content(
        f"""You are Zara, Abdul's AI assistant.
        Based on this document content:
        {pdf_text}
        Answer this question: {question}
        If the answer is not in the document, 
        say 'This information is not in the document.'"""
    )
    return response.text
def ask_with_image(question, image_path):
    try:
        image = PIL.Image.open(image_path)
        response = model.generate_content(
            [question, image]
        )
        return response.text
    except FileNotFoundError:
        return "Image file not found. Please check the path."
    except Exception as e:
        return f"Error: {e}"
system_prompt = """You are Abdul's personal AI assistant.
    Your name is Zara.
    You are helpful, friendly, and concise.
    Rules:
        - Always respond in the same language the user writes in
        - Keep answers clear and to the point
        - If asked a coding question, always provide code examples
        - End every response with one relevant follow-up question
        - Never give harmful or inappropriate content"""
def ask_groq(question, system_prompt):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # or another available Groq model
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )
    return response.choices[0].message.content
def ask_tavily(question):
    response = tavily_client.search(
        query=question,
        max_results=5)
    return response
def save_history(question , answer):
    if conn==None:
        return
    else:
        try:
            cursor=conn.cursor()
            cursor.execute(
                "INSERT INTO history (Chat) VALUES (?)",
                (question + " - " + answer,)
                )
            cursor.commit()
        except Exception as e:
            print(f"⚠️  Could not save to history: {e}")
model = genai.GenerativeModel('gemini-2.5-flash')
chat_session=model.start_chat(history=[])
print("Welcome to Abdul's personal AI assistant, Zara! 😍🥰")
print("1. Gemini (Google) — Free")
print("2. Groq (Anthropic) — Fast")
print("3. Tavily (Tavily) — Accurate for websearch")
ai_choice=input("Enter your choice (1, 2, or 3): ")
print(f"Zara has connected to {ai_choice}")
print("-" *50)
print("You want to use ai as:")
print("""
    1. Reasoning assistant.
    2. Customer classifier.
    3. Code reviewer.
    4. Content summarizer.
    5. Email writer.
    6. Study planner.
    7. JSON format.
    8. Table format.
    9. Strict assistant. 
""")
ai_fun=int(input("Enter your choice (1-9): "))
prompt_map = {
    1: pl.DEFAULT,
    2: pl.CUSTOMER_CLASSIFIER,
    3: pl.CODE_REVIEWER,
    4: pl.CONTENT_SUMMARIZER,
    5: pl.EMAIL_WRITER,
    6: pl.STUDY_PLANNER,
    7: pl.JSON_FORMAT,
    8: pl.TABLE_FORMAT,
    9: pl.STRICT_ASSISTANT
}
while True:
    print("1. Ask a question")
    print("2. Ask about an image")
    print("3. Ask about a PDF") 
    print("4. View history")
    print("5. new conversation ")
    print("6. Delete history")
    print("7. Switch AI model")
    print("8. Exit")
    try:
        choice=int(input("Enter your choice: "))
    except ValueError:
        print("Enter a choice between 1-10")
    if choice==1:
        selected_prompt = prompt_map.get(ai_fun, pl.DEFAULT)
        if ai_choice=="1":
            question = input("Enter your question: ")
            answer=chat_session.send_message(selected_prompt + question)
            answer = answer.text
            print("Answer:", answer)
            save_history(question, answer)
        elif ai_choice=="2":
            question=input("Enter your question: ")
            answer=ask_groq(question, selected_prompt)
            print("Answer:", answer)
            save_history(question, answer)
        elif ai_choice=="3":
            question=input("Enter your question: ")
            search_result=ask_tavily(question)
            ans=" "
            for result in search_result.get("results", []):
                title=result["title"]
                content=result["content"][:200]
                ans+=f"Title: {title}\nContent: {content}\n\n"
            answer=model.generate_content(f"""Based on these web search results:
            {ans}
            Answer this question clearly: {question}""")
            print("Answer:", answer.text)
            save_history(question, answer)
    elif choice==2:
        image_path = input("Enter image path: ")
        question = input("Enter your question about the image: ")
        answer = ask_with_image(question, image_path)
        print("\nZara:", answer)
        save_history(question, answer)
    elif choice == 3:
        pdf_path = input("Enter PDF path: ")
        print("\nWhat do you want to do with this PDF?")
        print("1. Summarize the document")
        print("2. Ask a specific question")
        print("3. Extract key points")
        pdf_choice = input("Enter choice (1-3): ")
        if pdf_choice == "1":
            question = "Summarize this document in a clear and concise way. Include main topics, key points and conclusion."
        elif pdf_choice == "2":
            question = input("Enter your question about the PDF: ")
        elif pdf_choice == "3":
            question = "Extract and list all the key points and important information from this document."
        else:
            question = "Summarize this document."
        answer = ask_about_pdf(question, pdf_path)
        print("\nZara:", answer)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO history (Chat) VALUES (?)",
            (f"[PDF: {pdf_path}] {question} - {answer}",)
        )   
        conn.commit()
    elif choice==4:
        if conn==None:
            print("Connect SQL server for checking")
        else:
            cursor=conn.cursor()
            cursor.execute("SELECT * FROM history")
            rows=cursor.fetchall()
            if not rows:
                print("No history found.")
            else:
                print("History:")
                for row in rows:
                    print(row.Chat)
    elif choice==5:
        chat_session=model.start_chat(history=[])
        chat_session.send_message(pl.DEFAULT)
        print("✅ New conversation started! Zara's memory cleared.")
    elif choice==6:
        cursor=conn.cursor()
        cursor.execute("SELECT * FROM history")
        rows=cursor.fetchall()
        if not rows:
            print("No history found.")
        else:
            cursor.execute("DELETE FROM history")
            conn.commit()
            print("History deleted successfully.")
    elif choice==7:
        print("1. Gemini (Google) — Free")
        print("2. Groq — Fast")
        print("3. GPT (OpenAI) — Popular")
        ai_choice=input("Enter your choice (1, 2, or 3): ")
        print("AI switched successfully!")
    elif choice==8:
        print("Thanks a lot for using our service. Bye!😍🥰")
        break
    else:
        print("Invalid choice. Please try again.")