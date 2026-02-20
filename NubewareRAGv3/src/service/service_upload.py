import os
import hashlib
import uuid
import requests
from flask import request, jsonify
from werkzeug.utils import secure_filename
import chromadb
from chromadb.config import Settings

DATA_FOLDER = "data"
CHROMA_PATH = "chroma_db"
EMBED_MODEL = "nomic-embed-text"
MAX_FILE_SIZE_MB = 15
CHUNK_SIZE = 800
OVERLAP = 100
BATCH_SIZE = 16


def upload_document(file):

    # ------------------------
    # 1️⃣ Validaciones básicas
    # ------------------------

    file = request.files["file"]

    if file.filename == "":
        return ({"error": "Empty filename"}), 400

    if len(file.read()) > MAX_FILE_SIZE_MB * 1024 * 1024:
        return ({"error": "File too large"}), 400

    file.seek(0)

    # ------------------------
    # 2️⃣ Guardar archivo
    # ------------------------
    os.makedirs(DATA_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(DATA_FOLDER, filename)
    file.save(file_path)

    # ------------------------
    # 3️⃣ Hash para evitar reprocesar
    # ------------------------
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # ------------------------
    # 4️⃣ Inicializar Chroma
    # ------------------------
    client = chromadb.Client(
        Settings(persist_directory=CHROMA_PATH)
    )

    collection = client.get_or_create_collection("documents")

    # Verificar si ya existe hash
    existing = collection.get(where={"file_hash": file_hash})
    if existing["ids"]:
        return jsonify({
            "message": "Document already indexed",
            "file_hash": file_hash
        }), 200

    # ------------------------
    # 5️⃣ Extraer texto (solo txt por ahora)
    # ------------------------
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    if not text.strip():
        return jsonify({"error": "Empty document"}), 400

    # ------------------------
    # 6️⃣ Chunking optimizado
    # ------------------------
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += CHUNK_SIZE - OVERLAP

    # ------------------------
    # 7️⃣ Procesar en batches
    # ------------------------
    total_chunks = len(chunks)
    processed = 0

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]

        embeddings = []
        ids = []
        metadatas = []

        for idx, chunk in enumerate(batch_chunks):

            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": EMBED_MODEL,
                    "prompt": chunk   # 🔥 CORRECTO
                }
            )

            if response.status_code != 200:
                return jsonify({"error": "Embedding generation failed"}), 500

            embedding = response.json()["embedding"]

            embeddings.append(embedding)
            ids.append(str(uuid.uuid4()))
            metadatas.append({
                "filename": filename,
                "file_hash": file_hash,
                "chunk_index": i + idx
            })

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=batch_chunks,
            metadatas=metadatas
        )

        processed += len(batch_chunks)
    # ------------------------
    # 8️⃣ Respuesta final
    # ------------------------
    return ({
        "message": "Document indexed successfully",
        "filename": filename,
        "file_hash": file_hash,
        "chunks_processed": processed
    }), 201