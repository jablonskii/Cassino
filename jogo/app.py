from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import eventlet
import randon

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura'
socketio = SocketIO(app)

usuarios = {} 
jogos = ["Caça-Níquel de Frutas", "Roleta da Sorte", "Blackjack Digital"]

@app.route('/')
def home():
    # A página inicial agora redireciona para o login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in usuarios and usuarios[username] == password:
            session['username'] = username
            return redirect(url_for('escolher_jogo'))
        return render_template('login.html', error="Usuário ou senha inválidos.")
    # Se for GET, apenas mostra a página de login
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in usuarios:
            return render_template('register.html', error="Este nome de usuário já existe.")
        usuarios[username] = password
        session['username'] = username
        return redirect(url_for('escolher_jogo'))
    # Se for GET, apenas mostra a página de registro
    return render_template('register.html')

@app.route('/jogos')
def escolher_jogo():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('jogos.html', usuario=session['username'], lista_jogos=jogos)

# (Mantenha todo o código existente no app.py)
# ...

# Adicione a biblioteca random se ainda não tiver


# --- DEFINIÇÕES DA ROLETA ---
# Mapeamento de números para cores
numeros_vermelhos = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
numeros_pretos = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

def get_cor(numero):
    if numero in numeros_vermelhos:
        return 'vermelho'
    if numero in numeros_pretos:
        return 'preto'
    return 'verde' # Para o zero

# --- NOVA ROTA PARA O JOGO ---
@app.route('/roleta')
def roleta():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('roleta.html', usuario=session['username'])

# --- NOVO EVENTO DE SOCKET PARA PROCESSAR A JOGADA ---
@socketio.on('girar_roleta')
def handle_roleta_spin(data):
    if 'username' not in session:
        return # Ignora se o usuário não estiver logado

    tipo_aposta = data.get('tipo')
    valor_aposta = float(data.get('valor'))
    escolha = data.get('escolha')

    # 1. Girar a roleta
    numero_sorteado = random.randint(0, 36)
    cor_sorteada = get_cor(numero_sorteado)
    
    ganhou = False
    valor_ganho = 0

    # 2. Verificar se o jogador ganhou
    if tipo_aposta == 'numero' and int(escolha) == numero_sorteado:
        ganhou = True
        valor_ganho = valor_aposta * 35
    elif tipo_aposta == 'cor' and escolha == cor_sorteada:
        ganhou = True
        valor_ganho = valor_aposta * 2
    elif tipo_aposta == 'par_impar' and numero_sorteado != 0:
        if escolha == 'par' and numero_sorteado % 2 == 0:
            ganhou = True
            valor_ganho = valor_aposta * 2
        elif escolha == 'impar' and numero_sorteado % 2 != 0:
            ganhou = True
            valor_ganho = valor_aposta * 2

    # 3. Enviar o resultado de volta para o jogador
    resultado_pessoal = {
        'numero': numero_sorteado,
        'cor': cor_sorteada,
        'ganhou': ganhou,
        'valor_ganho': valor_ganho
    }
    emit('resultado_roleta', resultado_pessoal)

    # 4. Se ganhou, anunciar no chat global
    if ganhou:
        anuncio_global = {
            'jogador': session['username'],
            'jogo': 'Roleta da Sorte',
            'valor': f"{valor_ganho:.2f}".replace('.', ',')
        }
        emit('novo_ganho', anuncio_global, broadcast=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('enviar_ganho_manual')
def handle_manual_win(data):
    emit('novo_ganho', data, broadcast=True)

# O if __name__ == '__main__' é para rodar localmente, não será usado no deploy
if __name__ == '__main__':
    socketio.run(app, debug=True)