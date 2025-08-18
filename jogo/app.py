from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura'
socketio = SocketIO(app)

# Banco de dados em memória para usuários
usuarios = {} 

# Lista de jogos disponíveis
jogos = ["Caça-Níquel de Frutas", "Roleta da Sorte", "Blackjack Digital"]

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('escolher_jogo'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username in usuarios and usuarios[username] == password:
        session['username'] = username
        return redirect(url_for('escolher_jogo'))
    
    return render_template('login.html', error="Usuário ou senha inválidos.")

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    if username in usuarios:
        # Retorna para a página de login mostrando o erro no formulário de registro
        return render_template('login.html', register_error="Este nome de usuário já existe.")
    
    # Cria o usuário
    usuarios[username] = password
    # Loga o usuário na sessão
    session['username'] = username
    # Redireciona direto para a página de jogos
    return redirect(url_for('escolher_jogo'))

@app.route('/jogos')
def escolher_jogo():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    return render_template('jogos.html', usuario=session['username'], lista_jogos=jogos)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@socketio.on('enviar_ganho_manual')
def handle_manual_win(data):
    # Emite a mensagem para todos os clientes conectados
    emit('novo_ganho', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)