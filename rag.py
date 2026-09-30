import os
import json
import numpy as np

import fitz
import pytesseract

from PIL import Image
from io import BytesIO

from ollama import embed, chat


# ============================================================
# SETTINGS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOCUMENT_FOLDER = os.path.join(BASE_DIR, "documents")

STORE_FILE = os.path.join(BASE_DIR, "rag_store.json")

# Tesseract installation location
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Ollama models
EMBEDDING_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"

# RAG settings
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 3


# ============================================================
# 1. READ PDF USING OCR
# ============================================================

def load_documents():

    print()
    print("Reading documents using OCR...")
    print()

    all_text = ""

    # Check documents folder
    if not os.path.exists(DOCUMENT_FOLDER):

        print("ERROR: documents folder not found.")

        return ""

    # Find PDF files
    pdf_files = [
        file
        for file in os.listdir(DOCUMENT_FOLDER)
        if file.lower().endswith(".pdf")
    ]

    if not pdf_files:

        print("ERROR: No PDF found inside documents folder.")

        return ""

    # Check Tesseract
    if not os.path.exists(TESSERACT_PATH):

        print("ERROR: Tesseract was not found.")
        print(TESSERACT_PATH)

        return ""

    # Tell pytesseract where Tesseract is
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    # Read every PDF
    for filename in pdf_files:

        filepath = os.path.join(
            DOCUMENT_FOLDER,
            filename
        )

        print("Reading:", filename)

        # Open PDF
        pdf = fitz.open(filepath)

        total_pages = len(pdf)

        print("Total pages:", total_pages)
        print()

        # Process every page
        for page_number, page in enumerate(pdf):

            print(
                f"OCR page {page_number + 1}/{total_pages}"
            )

            # Convert PDF page to image
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image_bytes = pix.tobytes("png")

            # Convert bytes to PIL image
            image = Image.open(
                BytesIO(image_bytes)
            )

            # OCR
            text = pytesseract.image_to_string(
                image
            )

            # Store extracted text
            if text.strip():

                all_text += text
                all_text += "\n"

        pdf.close()

        print()
        print("Finished:", filename)

    print()
    print("OCR completed.")

    print(
        "Extracted characters:",
        len(all_text)
    )

    return all_text


# ============================================================
# 2. SPLIT TEXT INTO CHUNKS
# ============================================================

def create_chunks(text):

    print()
    print("Creating text chunks...")

    chunks = []

    start = 0

    while start < len(text):

        end = start + CHUNK_SIZE

        chunk = text[start:end].strip()

        if chunk:

            chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP

    print(
        "Chunks created:",
        len(chunks)
    )

    return chunks


# ============================================================
# 3. CREATE EMBEDDINGS
# ============================================================

def create_embeddings(chunks):

    print()
    print("Creating embeddings...")
    print()

    embeddings = []

    total = len(chunks)

    for i, chunk in enumerate(chunks):

        print(
            f"Embedding {i + 1}/{total}"
        )

        try:

            response = embed(
                model=EMBEDDING_MODEL,
                input=chunk
            )

            embedding = response["embeddings"][0]

            embeddings.append(embedding)

        except Exception as e:

            print()
            print(
                "ERROR while creating embedding:"
            )

            print(e)

            return []

    print()
    print("Embeddings created successfully.")

    return embeddings


# ============================================================
# 4. CREATE RAG DATABASE
# ============================================================

def create_rag_database():

    # Read PDF
    text = load_documents()

    if not text:

        print()
        print("No text found in PDF.")
        print("Database creation failed.")

        return False

    # Create chunks
    chunks = create_chunks(text)

    if not chunks:

        print()
        print("No chunks were created.")
        print("Database creation failed.")

        return False

    # Create embeddings
    embeddings = create_embeddings(chunks)

    if not embeddings:

        print()
        print("Embedding creation failed.")
        print("Database creation failed.")

        return False

    # Create database
    database = []

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):

        database.append(
            {
                "text": chunk,
                "embedding": embedding
            }
        )

    # Save database
    print()
    print("Saving RAG database...")

    try:

        with open(
            STORE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                database,
                file
            )

    except Exception as e:

        print()
        print("ERROR while saving database:")
        print(e)

        return False

    print()
    print("========================================")
    print(" RAG DATABASE CREATED SUCCESSFULLY")
    print("========================================")

    print(
        "Number of chunks:",
        len(database)
    )

    print(
        "Database file:",
        STORE_FILE
    )

    print()

    return True


# ============================================================
# 5. LOAD RAG DATABASE
# ============================================================

def load_rag_database():

    if not os.path.exists(STORE_FILE):

        print("RAG database not found.")

        return None

    try:

        with open(
            STORE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            database = json.load(file)

        return database

    except Exception as e:

        print("ERROR loading RAG database:")
        print(e)

        return None


# ============================================================
# 6. COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    a = np.array(a)

    b = np.array(b)

    denominator = (
        np.linalg.norm(a)
        *
        np.linalg.norm(b)
    )

    if denominator == 0:

        return 0

    similarity = (
        np.dot(a, b)
        /
        denominator
    )

    return similarity


# ============================================================
# 7. SEARCH RELEVANT DOCUMENT CHUNKS
# ============================================================

def search_documents(question):

    database = load_rag_database()

    if not database:

        return []

    # Create embedding for user's question
    try:

        response = embed(
            model=EMBEDDING_MODEL,
            input=question
        )

        question_embedding = response[
            "embeddings"
        ][0]

    except Exception as e:

        print()
        print("ERROR creating question embedding:")
        print(e)

        return []

    results = []

    # Compare question with every chunk
    for item in database:

        score = cosine_similarity(
            question_embedding,
            item["embedding"]
        )

        results.append(
            {
                "text": item["text"],
                "score": float(score)
            }
        )

    # Highest similarity first
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Return top chunks
    return results[:TOP_K]


# ============================================================
# 8. ASK LLAMA USING RETRIEVED INFORMATION
# ============================================================

def ask_question(question):

    print()
    print("Searching document...")

    results = search_documents(question)

    if not results:

        return (
            "I could not find relevant information "
            "in the document."
        )

    # Combine retrieved chunks
    context = "\n\n".join(
        result["text"]
        for result in results
    )

    # Prompt for Llama
    prompt = f"""
You are a helpful Java learning assistant.

You must answer the user's question using ONLY
the information provided in the CONTEXT.

Do not use outside knowledge.

If the answer is not available in the CONTEXT,
say:

"I could not find this information in the document."

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    try:

        response = chat(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response[
            "message"
        ]["content"]

        return answer

    except Exception as e:

        return (
            "Error while communicating with Ollama: "
            + str(e)
        )


# ============================================================
# 9. MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    print()
    print("====================================")
    print("          RAG CHATBOT")
    print("====================================")

    # --------------------------------------------------------
    # Check if database exists
    # --------------------------------------------------------

    if not os.path.exists(STORE_FILE):

        print()
        print("RAG database does not exist.")
        print("Creating database...")

        success = create_rag_database()

        if not success:

            print()
            print("Database creation failed.")

            exit()

    else:

        print()
        print("RAG database already exists.")

    # --------------------------------------------------------
    # Start chatbot
    # --------------------------------------------------------

    print()
    print("====================================")
    print("       RAG CHATBOT READY")
    print("====================================")

    print()
    print("You can now ask questions.")
    print("Type 'exit' to stop.")
    print()

    while True:

        question = input("You: ")

        # Exit
        if question.lower().strip() == "exit":

            print("Goodbye!")

            break

        # Ignore empty questions
        if not question.strip():

            continue

        # Get answer
        answer = ask_question(question)

        print()
        print("Bot:", answer)
        print()