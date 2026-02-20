# chroma_inspect.py - corre esto como script independiente
import chromadb

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("documents")

# Ver todos los chunks y sus metadatos
results = collection.get(include=["metadatas"])

print("Total chunks:", len(results["ids"]))
for i, meta in enumerate(results["metadatas"]):
    print(f"Chunk {i}: {meta}")