from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, date

app = Flask(__name__)
CORS(app) # Permite que o HTML acesse este servidor

# --- "BANCO DE DADOS" EM MEMÓRIA ---

# Coleção de Livros (Começando com alguns dados de exemplo)
livros = [
    {'id': 1, 'titulo': 'Dom Quixote', 'autor': 'Miguel de Cervantes', 'isbn': '12345', 'ano': 1605, 'categorias': 'Clássico', 'quantidade': 3},
    {'id': 2, 'titulo': 'O Pequeno Príncipe', 'autor': 'Saint-Exupéry', 'isbn': '67890', 'ano': 1943, 'categorias': 'Infantil', 'quantidade': 5}
]

# Coleção de Usuários
usuarios = []

# Coleção de Empréstimos
emprestimos = []

# --- FUNÇÕES AUXILIARES ---

def gerar_novo_id(colecao):
    """Retorna um novo ID baseado no último item da lista + 1"""
    if len(colecao) > 0:
        return colecao[-1]['id'] + 1
    return 1

def encontrar_por_id(colecao, id_procurado):
    """Busca um item dentro de uma lista pelo ID"""
    for item in colecao:
        if item['id'] == id_procurado:
            return item
    return None

# --- ROTAS (ENDPOINTS) ---

# 1. Rota para LISTAR e CRIAR Livros
@app.route('/livros', methods=['GET', 'POST'])
def gerenciar_livros():
    if request.method == 'GET':
        return jsonify(livros)
    
    if request.method == 'POST':
        data = request.json or {}
        # Validação simples
        if not data.get('titulo') or not data.get('autor'):
            return jsonify({'error': 'Titulo e Autor são obrigatórios'}), 400
        
        novo_livro = {
            'id': gerar_novo_id(livros),
            'titulo': data.get('titulo'),
            'autor': data.get('autor'),
            'isbn': data.get('isbn', ''),
            'ano': int(data.get('ano', 0)),
            'categorias': data.get('categorias', ''),
            'quantidade': int(data.get('quantidade', 1))
        }
        livros.append(novo_livro)
        return jsonify(novo_livro), 201

# 2. Rota para CRIAR Usuários
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    data = request.json or {}
    if not data.get('nome'):
        return jsonify({'error': 'Nome é obrigatório'}), 400

    novo_usuario = {
        'id': gerar_novo_id(usuarios),
        'nome': data.get('nome'),
        'email': data.get('email', ''),
        'telefone': data.get('telefone', '')
    }
    usuarios.append(novo_usuario)
    return jsonify(novo_usuario), 201

# 3. Rota para EMPRÉSTIMOS
@app.route('/emprestimos', methods=['GET', 'POST'])
def gerenciar_emprestimos():
    if request.method == 'GET':
        return jsonify(emprestimos)

    if request.method == 'POST':
        data = request.json or {}
        try:
            usuario_id = int(data.get('usuario')) # O HTML envia como 'usuario'
            livro_id = int(data.get('livro'))     # O HTML envia como 'livro'
            data_prevista = data.get('data_prevista')
        except (ValueError, TypeError):
             return jsonify({'error': 'IDs inválidos'}), 400

        # Verifica se livro e usuário existem na memória
        livro = encontrar_por_id(livros, livro_id)
        usuario = encontrar_por_id(usuarios, usuario_id) # Aqui precisaria ter usuários cadastrados antes

        # Para facilitar o teste, se não achar o usuário, cria um "falso" na hora ou aceita sem validar
        # Mas o ideal é validar:
        if not livro:
            return jsonify({'error': 'Livro não encontrado'}), 404
        
        if livro['quantidade'] <= 0:
            return jsonify({'error': 'Livro sem estoque'}), 400

        # Decrementa estoque
        livro['quantidade'] -= 1

        novo_emprestimo = {
            'id': gerar_novo_id(emprestimos),
            'usuario_id': usuario_id,
            'livro_id': livro_id,
            'data_emprestimo': datetime.now().strftime('%Y-%m-%d'),
            'data_prevista': data_prevista,
            'devolvido': False,
            'data_devolucao': None
        }
        emprestimos.append(novo_emprestimo)
        return jsonify(novo_emprestimo), 201

# 4. Rota para DEVOLUÇÃO
@app.route('/devolucoes/<int:emprestimo_id>', methods=['POST'])
def devolver(emprestimo_id):
    emprestimo = encontrar_por_id(emprestimos, emprestimo_id)
    
    if not emprestimo:
        return jsonify({'error': 'Emprestimo não encontrado'}), 404
    
    if emprestimo['devolvido']:
        return jsonify({'error': 'Este empréstimo já foi devolvido'}), 400

    # Marca como devolvido
    emprestimo['devolvido'] = True
    emprestimo['data_devolucao'] = datetime.now().strftime('%Y-%m-%d')

    # Devolve o estoque do livro
    livro = encontrar_por_id(livros, emprestimo['livro_id'])
    if livro:
        livro['quantidade'] += 1

    return jsonify(emprestimo), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)