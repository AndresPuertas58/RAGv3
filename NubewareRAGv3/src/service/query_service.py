import requests
import ollama
from flask import request, jsonify
import chromadb
from chromadb.config import Settings

CHROMA_PATH = "chroma_db"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"
TOP_K = 3


def ask_question():

    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400

    question = data["question"]

    # 1️⃣ Generar embedding
    embed_response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": EMBED_MODEL,
            "prompt": question  # 🔥 corregido
        }
    )

    if embed_response.status_code != 200:
        return jsonify({
            "error": "Failed to generate question embedding",
            "details": embed_response.text
        }), 500

    embed_json = embed_response.json()

    if "embedding" not in embed_json:
        return jsonify({"error": "Invalid embedding response"}), 500

    query_embedding = embed_json["embedding"]

    # 2️⃣ Consultar Chroma
    client = chromadb.Client(
        Settings(persist_directory=CHROMA_PATH)
    )

    collection = client.get_or_create_collection("documents")

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K
    )

    documents = results.get("documents")

    # 3️⃣ Si no hay contexto → LLM directo
    if not documents or len(documents) == 0 or len(documents[0]) == 0:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": question}
            ]
        )

        return jsonify({
            "answer": response["message"]["content"],
            "source": "llm_direct"
        })

    # 4️⃣ Si hay contexto → RAG
    context = "\n".join(documents[0])

    prompt = f"""
Responde usando el siguiente contexto:

{context}

Pregunta:
{question}
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return jsonify({
        "answer": response["message"]["content"],
        "source": "rag"
    })