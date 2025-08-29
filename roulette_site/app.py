import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_bcrypt import Bcrypt
import random

# ===================================================================
# CONFIGURAÇÃO DA APLICAÇÃO E BASE DE DADOS
# ===================================================================
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_dificil_de_adivinhar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'game.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redireciona utilizadores não logados para a página de login
login_manager.login_message_category = 'info'
login_manager.login_message = "Por favor, faça login para aceder a esta página."

# ===================================================================
# MODELOS DA BASE DE DADOS (TABELAS)
# ===================================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    # NOVO: Campo para guardar o saldo do utilizador
    bankroll = db.Column(db.Float, nullable=False, default=1000.0)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# ===================================================================
# FORMULÁRIOS DE LOGIN E REGISTO (WTForms)
# ===================================================================
class RegistrationForm(FlaskForm):
    username = StringField('Nome de Utilizador', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de utilizador já existe. Por favor, escolha outro.')

class LoginForm(FlaskForm):
    username = StringField('Nome de Utilizador', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Login')

# ===================================================================
# LÓGICA DO JOGO DE ROLETA (Funções Auxiliares)
# ===================================================================
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}

def spin_wheel():
    pockets = ['00', 0] + list(range(1, 37))
    return random.choice(pockets)

def color_of(n):
    if n in (0, '00'): return 'green'
    return 'red' if n in RED else 'black'

def parity_of(n):
    if n in (0, '00'): return None
    return 'even' if (n % 2 == 0) else 'odd'

def dozen_of(n):
    if n in (0, '00'): return None
    if 1 <= n <= 12: return '1st12'
    if 13 <= n <= 24: return '2nd12'
    return '3rd12'

def column_of(n):
    if n in (0, '00'): return None
    rem = ((n - 1) % 3) + 1
    return f'col{rem}'

def half_of(n):
    if n in (0, '00'): return None
    return '1to18' if 1 <= n <= 18 else '19to36'

PAYOUTS = { 'straight': 35, 'red': 1, 'black': 1, 'even': 1, 'odd': 1, '1st12': 2, '2nd12': 2, '3rd12': 2, 'col1': 2, 'col2': 2, 'col3': 2, '1to18': 1, '19to36': 1 }

# ===================================================================
# ROTAS DA APLICAÇÃO (PÁGINAS)
# ===================================================================

@app.route('/')
@login_required # Protege a página principal, só utilizadores logados podem aceder
def index():
    # Passa o saldo do utilizador atual para o template
    return render_template('index.html', bankroll=current_user.bankroll)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login falhou. Verifique o nome de utilizador e a senha.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        # O saldo inicial de 1000 é definido por defeito no modelo
        db.session.add(user)
        db.session.commit()
        flash('A sua conta foi criada! Agora pode fazer login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registo', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/spin', methods=['POST'])
@login_required # Protege o endpoint de giro
def spin():
    data = request.get_json(silent=True) or {}
    bets = data.get('bets', [])
    
    # Validação do lado do servidor
    total_bet_amount = sum(float(bet.get('amount', 0)) for bet in bets)
    if total_bet_amount > current_user.bankroll:
        return jsonify({'error': 'Saldo insuficiente'}), 400

    # Desconta o valor apostado do saldo do utilizador
    current_user.bankroll -= total_bet_amount
    
    result = spin_wheel()
    color = color_of(result)
    
    total_win = 0.0
    for bet in bets:
        kind = bet.get('type')
        value = bet.get('value')
        amount = float(bet.get('amount', 0))
        win = 0.0
        
        # Lógica de verificação de apostas...
        if kind == 'straight' and str(value) == str(result):
            win = amount * (PAYOUTS['straight'] + 1)
        elif kind in ('red','black') and color == kind:
            win = amount * (PAYOUTS[kind] + 1)
        # Adicione outras verificações (even/odd, etc.) aqui...
        
        total_win += win

    # Adiciona os ganhos ao saldo do utilizador
    current_user.bankroll += total_win
    db.session.commit() # Salva as alterações na base de dados

    return jsonify({
        'result': result,
        'color': color,
        'total_win': total_win,
        'new_bankroll': current_user.bankroll # Envia o novo saldo para o frontend
    })

if __name__ == '__main__':
    app.run(debug=True)
