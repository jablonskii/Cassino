from flask import render_template, url_for, flash, redirect, request, jsonify
from app import app, db
from app.forms import RegistrationForm, LoginForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
import random

# --- Lógica da Roleta (do seu app.py antigo) ---
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
PAYOUTS = { 'straight': 35, 'red': 1, 'black': 1, 'even': 1, 'odd': 1, '1st12': 2, '2nd12': 2, '3rd12': 2, 'col1': 2, 'col2': 2, 'col3': 2, '1to18': 1, '19to36': 1 }
def spin_wheel():
    pockets = ['00', 0] + list(range(1, 37))
    return random.choice(pockets)
def color_of(n):
    if n in (0, '00'): return 'green'
    return 'red' if n in RED else 'black'
# ... (adicione as outras funções auxiliares da roleta aqui: parity_of, dozen_of, etc.)

# --- Rotas de Utilizador (do ZIP) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login falhou. Verifique os seus dados.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso! Pode fazer login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registo', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Rotas do Jogo (Modificadas) ---
@app.route('/')
@login_required
def index():
    return render_template('index.html', bankroll=current_user.bankroll)

@app.route('/spin', methods=['POST'])
@login_required
def spin():
    data = request.get_json(silent=True) or {}
    bets = data.get('bets', [])
    
    total_bet_amount = sum(float(bet.get('amount', 0)) for bet in bets)
    if total_bet_amount > current_user.bankroll:
        return jsonify({'error': 'Saldo insuficiente'}), 400

    current_user.bankroll -= total_bet_amount
    
    result = spin_wheel()
    color = color_of(result)
    
    total_win = 0.0
    for bet in bets:
        # ... (a sua lógica de cálculo de ganhos completa vai aqui) ...
        if bet.get('type') == 'straight' and str(bet.get('value')) == str(result):
             win = float(bet.get('amount', 0)) * (PAYOUTS['straight'] + 1)
             total_win += win
        # ... etc para as outras apostas

    current_user.bankroll += total_win
    db.session.commit()

    return jsonify({
        'result': result,
        'color': color,
        'total_win': total_win,
        'new_bankroll': current_user.bankroll
    })
