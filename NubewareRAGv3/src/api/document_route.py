from flask import Blueprint, jsonify, request
from service.service_upload import upload_document


document_bp = Blueprint("document", __name__)

@document_bp.route("/documents/upload", methods=["POST"])
def subir():
    if "file" not in request.files:
        return jsonify({"error": "No se encontró el archivo en la petición"}), 400

    file = request.files["file"]

    response, status_code = upload_document(file)
    return jsonify(response), status_code