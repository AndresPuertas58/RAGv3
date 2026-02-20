from flask import Flask, request, jsonify
from service.service_upload import upload_document
from service.query_service import ask_question
from api.rag_routes import rag_bp
from api.document_route import document_bp
from flask_cors import CORS



app = Flask(__name__)

CORS(app)

@app.route("/hola", methods=["GET"])
def saludar():
    message = "hola"
    return message
saludar()

#Registrar los decoradores de la ruta para que al el servidor flask los reconozca 
app.register_blueprint(rag_bp)
app.register_blueprint(document_bp)



if __name__ == "__main__":
    app.run(debug=True, port=5078, host="0.0.0.0")