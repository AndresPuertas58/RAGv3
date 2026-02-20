from flask import Blueprint, jsonify
from service.query_service import ask_question

rag_bp = Blueprint("rag", __name__)

#END POINT QUE RECIBE LA PREGUNTA DESDE EL FRONTED Y PROCESA LA RESPUESTA
@rag_bp.route("/ask", methods=["POST"])
def preguntar():
    response, status_code = ask_question()
    return jsonify(response), status_code