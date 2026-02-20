import os
import hashlib
import uuid
import requests
from flask import request, jsonify
from werkzeug.utils import secure_filename
import chromadb
from chromadb.config import Settings
from config import get_db_connection


DATA_FOLDER = "data"
CHROMA_PATH = "chroma_db"
EMBED_MODEL = "nomic-embed-text"
MAX_FILE_SIZE_MB = 15
CHUNK_SIZE = 800
OVERLAP = 100
BATCH_SIZE = 16

#Metodo para devolver chromas
def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)

#Consultar lista de Documentos
def list_documents():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, filename, chunks_count, created_at FROM documents ORDER BY created_at DESC")
    docs = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    for doc in docs:
        if doc["created_at"]:
            doc["created_at"] = doc["created_at"].isoformat()
    
    return {"documents": docs}, 200


#METODO Y FLUJO DE CARGA, VECTORIZACION, CREACION DE ID REFERENTE AL CHROMA Y DOCUMENTO Y ALOJAMIENTO EN db
def upload_document():

    file = request.files.get("file")

    if not file or file.filename == "":
        return ({"error": "Empty filename"}), 400

    if len(file.read()) > MAX_FILE_SIZE_MB * 1024 * 1024:
        return ({"error": "File too large"}), 400
    file.seek(0)

    # Guardar archivo
    os.makedirs(DATA_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(DATA_FOLDER, filename)
    file.save(file_path)

    # Hash del archivo
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Verificar si ya existe en MySQL
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM documents WHERE file_hash = %s", (file_hash,))
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        conn.close()
        return ({
            "message": "Document already indexed",
            "file_hash": file_hash,
            "document_id": existing["id"]
        }), 200

    # Extraer texto
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    if not text.strip():
        cursor.close()
        conn.close()
        return ({"error": "Empty document"}), 400

    # Chunking
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunks.append(" ".join(words[start:end]))
        start += CHUNK_SIZE - OVERLAP

    # Generar document_id único que vincula MySQL <-> Chroma
    document_id = str(uuid.uuid4())

    # Procesar embeddings y guardar en Chroma
    client = get_chroma_client()
    collection = client.get_or_create_collection("documents")

    total_chunks = len(chunks)
    processed = 0

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]

        embeddings, ids, metadatas = [], [], []

        for idx, chunk in enumerate(batch_chunks):
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": EMBED_MODEL, "prompt": chunk}
            )

            if response.status_code != 200:
                cursor.close()
                conn.close()
                return ({"error": "Embedding generation failed"}), 500

            embeddings.append(response.json()["embedding"])
            ids.append(str(uuid.uuid4()))
            metadatas.append({
                "document_id": document_id,   # 🔑 Vínculo con MySQL
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

    # Guardar registro en MySQL
    cursor.execute(
        """
        INSERT INTO documents (id, filename, file_hash, chunks_count)
        VALUES (%s, %s, %s, %s)
        """,
        (document_id, filename, file_hash, processed)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return ({
        "message": "Document indexed successfully",
        "document_id": document_id,
        "filename": filename,
        "file_hash": file_hash,
        "chunks_processed": processed
    }), 201