from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "biblioteca.db")

print("\nBanco de dados usado:")
print(DB_PATH, "\n")

app = Flask(__name__, static_folder="", template_folder="")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(50))
    ano = db.Column(db.Integer)
    categorias = db.Column(db.String(200))
    quantidade = db.Column(db.Integer, default=1)


class Emprestimo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(200), nullable=False)
    livro_id = db.Column(db.Integer, db.ForeignKey("livro.id"), nullable=False)
    data_emprestimo = db.Column(db.String(20))
    data_prevista = db.Column(db.String(20))
    devolvido = db.Column(db.Boolean, default=False)
    data_devolucao = db.Column(db.String(20))


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return send_from_directory("", "index.html")


@app.route("/<path:filename>")
def arquivos(filename):
    return send_from_directory("", filename)


@app.route("/livros", methods=["GET"])
def listar_livros():
    livros = Livro.query.all()
    return jsonify([
        {
            "id": l.id,
            "titulo": l.titulo,
            "autor": l.autor,
            "isbn": l.isbn,
            "ano": l.ano,
            "categorias": l.categorias,
            "quantidade": l.quantidade
        }
        for l in livros
    ])


@app.route("/livros", methods=["POST"])
def cadastrar_livro():
    data = request.json or {}

    if not data.get("titulo") or not data.get("autor"):
        return jsonify({"error": "Título e autor são obrigatórios"}), 400

    # Aceita tanto quantidade_total (frontend) quanto quantidade
    quantidade = data.get("quantidade_total") or data.get("quantidade") or 1

    livro = Livro(
        titulo=data["titulo"],
        autor=data["autor"],
        isbn=data.get("isbn", ""),
        ano=int(data.get("ano", 0)),
        categorias=data.get("categorias", ""),
        quantidade=int(quantidade)
    )

    db.session.add(livro)
    db.session.commit()

    return jsonify({"message": "Livro cadastrado com sucesso", "id": livro.id}), 201


@app.route("/emprestimos", methods=["GET"])
def listar_emprestimos():
    lista = Emprestimo.query.all()
    return jsonify([
        {
            "id": e.id,
            "usuario": e.usuario,
            "livro_id": e.livro_id,
            "data_emprestimo": e.data_emprestimo,
            "data_prevista": e.data_prevista,
            "devolvido": e.devolvido,
            "data_devolucao": e.data_devolucao
        }
        for e in lista
    ])


@app.route("/emprestimos", methods=["POST"])
def registrar_emprestimo():
    data = request.json or {}

    usuario = data.get("usuario")
    livro_id = data.get("livro")

    if not usuario or not livro_id:
        return jsonify({"error": "Usuário e Livro são obrigatórios"}), 400

    livro = Livro.query.get(livro_id)
    if not livro:
        return jsonify({"error": "Livro não encontrado"}), 404

    if livro.quantidade <= 0:
        return jsonify({"error": "Livro sem estoque disponível"}), 400

    # reduz estoque
    livro.quantidade -= 1

    emprestimo = Emprestimo(
        usuario=usuario,
        livro_id=livro_id,
        data_emprestimo=datetime.now().strftime("%Y-%m-%d"),
        data_prevista=data.get("data_prevista"),
        devolvido=False
    )

    db.session.add(emprestimo)
    db.session.commit()

    return jsonify({"message": "Empréstimo registrado com sucesso"}), 201


@app.route("/devolucao/<int:id>", methods=["POST"])
def devolver_livro(id):
    e = Emprestimo.query.get(id)

    if not e:
        return jsonify({"error": "Empréstimo não encontrado"}), 404

    if e.devolvido:
        return jsonify({"error": "Livro já devolvido"}), 400

    e.devolvido = True
    e.data_devolucao = datetime.now().strftime("%Y-%m-%d")

    livro = Livro.query.get(e.livro_id)
    livro.quantidade += 1

    db.session.commit()

    return jsonify({"message": "Devolução concluída com sucesso"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
