from langchain_community.embeddings.ollama import OllamaEmbeddings
#from langchain_community.embeddings.bedrock import BedrockEmbeddings


def get_embedding_function():
    #embeddings = BedrockEmbeddings(
    #    credentials_profile_name="default", region_name="us-east-1"
    #)
    embeddings = OllamaEmbeddings(base_url='http://127.0.0.1:11434',model="llama3:latest")#model="nomic-embed-text")
    return embeddings
