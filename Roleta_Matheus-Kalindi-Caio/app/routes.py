import random
from flask import render_template, url_for, flash, redirect, request, jsonify
from app import app, db
from app.forms import RegistrationForm, LoginForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required


RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK = set(range(1, 37)) - RED
PAYOUTS = {
    'straight': 35, 'red': 1, 'black': 1, 'even': 1, 'odd': 1,
    '1st12': 2, '2nd12': 2, '3rd12': 2, 'col1': 2, 'col2': 2, 'col3': 2,
    '1to18': 1, '19to36': 1
}

def spin_wheel():
    pockets = ['00', 0] + list(range(1, 37))
    return random.choice(pockets)

def color_of(n):
    if n in (0, '00'): return 'green'
    return 'red' if n in RED else 'black'

def parity_of(n):
    if not isinstance(n, int) or n == 0: return None
    return 'even' if (n % 2 == 0) else 'odd'

def dozen_of(n):
    if not isinstance(n, int) or n == 0: return None
    if 1 <= n <= 12: return '1st12'
    if 13 <= n <= 24: return '2nd12'
    return '3rd12'

def column_of(n):
    if not isinstance(n, int) or n == 0: return None
    rem = ((n - 1) % 3) + 1
    return f'col{rem}'

def half_of(n):
    if not isinstance(n, int) or n == 0: return None
    return '1to18' if 1 <= n <= 18 else '19to36'



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data) 
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('A sua conta foi criada com sucesso! Pode agora fazer login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Registo', form=form)

@app.route("/login", methods=['GET', 'POST'])
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
            flash('Login sem sucesso. Por favor, verifique o nome de utilizador e a senha.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template('index.html', bankroll=current_user.bankroll)

@app.route("/spin", methods=['POST'])
@login_required
def spin():
    data = request.get_json(silent=True) or {}
    bets = data.get('bets', [])
    
    total_bet_amount = sum(float(bet.get('amount', 0)) for bet in bets)
    if total_bet_amount > current_user.bankroll:
        return jsonify({'error': 'Saldo insuficiente.'}), 400

    current_user.bankroll -= total_bet_amount
    
    result = spin_wheel()
    color = color_of(result)
    
    total_win = 0.0
    for bet in bets:
        kind = bet.get('type')
        value = bet.get('value')
        amount = float(bet.get('amount', 0))
        
        won = False
        if kind == 'straight':
            if str(value) == str(result): won = True
        elif kind in ('red', 'black'):
            if color == kind: won = True
        elif kind in ('even', 'odd'):
            if parity_of(result) == kind: won = True
        elif kind in ('1st12', '2nd12', '3rd12'):
            if dozen_of(result) == kind: won = True
        elif kind in ('col1', 'col2', 'col3'):
            if column_of(result) == kind: won = True
        elif kind in ('1to18', '19to36'):
            if half_of(result) == kind: won = True
        
        if won:
            payout_multiplier = PAYOUTS.get(kind, 0)
            win_amount = amount * (payout_multiplier + 1)
            total_win += win_amount

    current_user.bankroll += total_win
    db.session.commit()

    return jsonify({
        'result': result,
        'color': color,
        'total_win': total_win,
        'new_bankroll': current_user.bankroll
    })
