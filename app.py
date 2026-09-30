from flask import Flask, request, jsonify, send_from_directory
from rag import ask_question
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "answer": "Please enter a question."
        })

    answer = ask_question(question)

    return jsonify({
        "answer": answer
    })


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


if __name__ == "__main__":

    print("Starting RAG Chatbot...")
    print("Open: http://127.0.0.1:5001")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5001
    )