import os
from flask import Flask, request, jsonify, send_file, send_from_directory,Response, make_response
from flask_sock import Sock
from werkzeug.utils import secure_filename
from werkzeug.wsgi import FileWrapper
from pprint import pprint 
import subprocess
import random
import io
from io import StringIO
import base64
from PIL import Image
import xml.etree.ElementTree as ET
import pandas as pd
#import pickle
import requests
import json
import urllib.parse
import string
import random
import smtplib, ssl
from email.mime.text import MIMEText
import os,re
#import paramiko
import time
import socket
import datetime

import argparse
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function



app = Flask(__name__)
sock = Sock(app)
path = os.getcwd()

ports = {
    "data_extraction": 5002
}
PREFIX = "/api"
port = int(os.environ.get("PORT", ports["data_extraction"]))
   

############### Gets an image to challenge the user #####################
@app.route(PREFIX+ '/rag_query',methods=['POST'])
def lxc_creator():
    result =[]
    data= request.json
    username        = data.get('username')
    query           = data.get('query')
    print("username: ", username, "query: ",query)
    response = query_rag(query)
    result.append(response)

    return jsonify(result)



CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Prepare the DB.
embedding_function = get_embedding_function()
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
model = Ollama(model="llama3:latest")

def query_rag(query_text: str):  
    # Search the DB.
    result =[]
    results = db.similarity_search_with_score(query_text, k=5)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    # print(prompt)
    #model = Ollama(model="mistral")
    response_text = model.invoke(prompt)
    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    response ={"status":"good","answer":str(response_text)}
    print(response)
    #result.append(response)
    return (response)





if __name__ == '__main__':
    #parser = argparse.ArgumentParser()
    #parser.add_argument("query_text", type=str, help="The query text.")
    #args = parser.parse_args()
    #query_text = args.query_text
    #query_rag(query_text)
    app.run(debug=True, host='0.0.0.0', port=port)


