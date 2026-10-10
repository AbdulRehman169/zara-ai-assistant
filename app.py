from flask import Flask, render_template, request, redirect, url_for
import zara_core as zara
import os
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # make sure the folder exists, or .save() crashes
AI_MODEL_MAP = {"gemini": 1, "groq": 2, "tavily": 3}
@app.route("/")
def home():
    return render_template("index.html", answer=None, question=None)
@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question")
    ai_model_word = request.form.get("ai_model")
    prompt_mode_str = request.form.get("prompt_mode")
    image_question= request.form.get("image_question")
    image_file = request.files.get("image")   # FIX: files come from request.files
    pdf_file= request.files.get("pdf")
    pdf_question= request.form.get("pdf_question")
    ai_choice = AI_MODEL_MAP.get(ai_model_word, 1)
    ai_fun = int(prompt_mode_str)
    # If a real image was uploaded, ask Zara ABOUT the image
    if image_file is not None and image_file.filename != "":
        save_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(save_path)
        # 1. Decide which question to ask
        if image_question:
            q_for_image = image_question
        else:
            q_for_image = "What do you see in this image?"
        question = q_for_image
        answer = zara.ask_with_image(question, save_path) 
    elif pdf_file is not None and pdf_file.filename!="":
        save_pathpdf=os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(save_pathpdf)
        if pdf_question:
            q_for_pdf= pdf_question
        else:
            q_for_pdf="Read pdf carefully and give its summary."
        question = q_for_pdf
        answer = zara.ask_about_pdf(question, save_pathpdf) 
    else:
        answer = zara.ask_zara(question)
    return render_template("index.html", answer=answer, question=question)
@app.route("/history")
def history():
    if zara.conn is None:
        return render_template("history.html", rows=None, error="No database connection.")
    try:
        cursor = zara.conn.cursor()
        cursor.execute("SELECT * FROM history")
        rows = cursor.fetchall()
        cursor.close()
        return render_template("history.html", rows=rows, error=None)
    except Exception as e:
        return render_template("history.html", rows=None, error=str(e))   
@app.route("/clear_history")
def clear_history():
    if zara.conn is None:
            return render_template("history.html", rows=None, error="No database connection.")
    try:
        cursor = zara.conn.cursor()
        cursor.execute("SELECT * FROM history")
        rows = cursor.fetchall()
        if rows:
            cursor = zara.conn.cursor()
            cursor.execute("DELETE FROM history")
            zara.conn.commit()
            cursor.close()
            return redirect (url_for("history"))
        else:
            return render_template("history.html", rows=None, error="History already empty.")
    except Exception as e:
        return render_template("history.html", rows=None, error=str(e))
@app.route("/start_new_conversation")
def start_new_conversation():
    zara.start_new_conversation()
    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)