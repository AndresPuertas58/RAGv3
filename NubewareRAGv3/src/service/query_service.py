import requests
import ollama
from flask import request
import chromadb
from chromadb.config import Settings
from config import get_db_connection

CHROMA_PATH = "chroma_db"
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"
TOP_K = 3

def ask_question():

    data = request.get_json()

    if not data or "question" not in data:
        return {"error": "Question is required"}, 400

    question = data["question"]
    document_ids = data.get("document_ids")
    

    # ------------------------
    # Validar document_ids en MySQL
    # ------------------------
    if document_ids:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        placeholders = ", ".join(["%s"] * len(document_ids))
        cursor.execute(
            f"SELECT id FROM documents WHERE id IN ({placeholders})",
            tuple(document_ids)
        )
        found = [row["id"] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        missing = [id for id in document_ids if id not in found]
        if missing:
            return {"error": "Documents not found", "missing_ids": missing}, 404

    # ------------------------
    # 1️⃣ Generar embedding
    # ------------------------
    embed_response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": question}
    )

    if embed_response.status_code != 200:
        return {"error": "Failed to generate question embedding", "details": embed_response.text}, 500

    embed_json = embed_response.json()

    if "embedding" not in embed_json:
        return {"error": "Invalid embedding response"}, 500

    query_embedding = embed_json["embedding"]
    

    # ------------------------
    # 2️⃣ Consultar Chroma
    # ------------------------
    client = chromadb.PersistentClient(path=CHROMA_PATH)  # ✅ PersistentClient
    collection = client.get_or_create_collection("documents")

    where_filter = None
    if document_ids:
        if len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        else:
            where_filter = {"document_id": {"$in": document_ids}}

    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": TOP_K,
        "include": ["documents", "metadatas", "distances"]
    }

    if where_filter:
        query_params["where"] = where_filter

    results = collection.query(**query_params)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    

    # ------------------------
    # 3️⃣ Sin contexto → LLM directo
    # ------------------------
    if not documents:
        print("✅ 4 - sin contexto, llamando LLM directo...")
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Eres un asistente útil. Responde de manera clara y concisa."},
                {"role": "user", "content": question}
            ]
        )
        return {
            "answer": response.message.content,
            "source": "llm_direct",
            "chunks_used": []
        }, 200

    # ------------------------
    # 4️⃣ Con contexto → RAG
    # ------------------------
    context = "\n\n---\n\n".join(documents)

    prompt = f"""Usa el siguiente contexto para responder la pregunta.
Si la respuesta no está en el contexto, indícalo claramente.

CONTEXTO:
{context}

PREGUNTA:
{question}

RESPUESTA:"""

    
    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "Eres un asistente experto. Responde basándote en el contexto proporcionado."},
            {"role": "user", "content": prompt}
        ]
    )
    

    chunks_used = [
        {
            "content": documents[i],
            "filename": metadatas[i].get("filename"),
            "document_id": metadatas[i].get("document_id"),
            "chunk_index": metadatas[i].get("chunk_index"),
            "distance": round(distances[i], 4)
        }
        for i in range(len(documents))
    ]

    return {
        "answer": response.message.content,
        "source": "rag",
        "chunks_used": chunks_used
    }, 200