from flask import Blueprint, jsonify, request
from service.service_upload import upload_document, list_documents, delete_document


document_bp = Blueprint("document", __name__)


#Endpoint que recibe los documentos e inicializa el metodo de vectorizacion y alojamiento en Chromas
@document_bp.route("/documents/upload", methods=["POST"])
def subir():
    if "file" not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files["file"]

    response, status_code = upload_document()
    return jsonify(response), status_code


#ENDPOINT PARA LISTAR LOS DOCUMENTOS CON CHROMAS ALOJADOS EN LA BASE DE DATOS 
#FUNCIONAL PARA LA ELECCION DE CHROMAS A CONSULTAR POR EL RAG

@document_bp.route("/documents", methods=["GET"])
def listar():
    response, status_code = list_documents()
    return jsonify(response), status_code    

# document_route.py - agregar este endpoint
@document_bp.route("/documents/<document_id>", methods=["DELETE"])
def eliminar(document_id):
    response, status_code = delete_document(document_id)
    return jsonify(response), status_code