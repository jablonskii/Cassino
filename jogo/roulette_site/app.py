
from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# Color map for numbers 1-36 in American roulette (same as European).
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = set(range(1,37)) - RED

def spin_wheel():
    # American roulette: 0, 00, and 1..36. We represent 00 as string '00'
    pockets = ['00', 0] + list(range(1, 37))
    result = random.choice(pockets)
    return result

def color_of(n):
    if n in (0, '00'):
        return 'green'
    return 'red' if n in RED else 'black'

def parity_of(n):
    if n in (0, '00'):
        return None
    return 'even' if (n % 2 == 0) else 'odd'

def dozen_of(n):
    if n in (0, '00'):
        return None
    if 1 <= n <= 12: return '1st12'
    if 13 <= n <= 24: return '2nd12'
    return '3rd12'

def column_of(n):
    if n in (0, '00'):
        return None
    # Columns on the layout (1,4,7,...), (2,5,8,...), (3,6,9,...)
    rem = ((n - 1) % 3) + 1
    return f'col{rem}'

def half_of(n):
    if n in (0, '00'):
        return None
    return '1to18' if 1 <= n <= 18 else '19to36'

# Payout ratios
PAYOUTS = {
    'straight': 35,
    'red': 1,
    'black': 1,
    'even': 1,
    'odd': 1,
    '1st12': 2,
    '2nd12': 2,
    '3rd12': 2,
    'col1': 2,
    'col2': 2,
    'col3': 2,
    '1to18': 1,
    '19to36': 1
}

@app.route('/')
def index():
    return render_template('index.html')

@app.post('/spin')
def spin():
    data = request.get_json(silent=True) or {}
    bets = data.get('bets', [])
    result = spin_wheel()
    color = color_of(result)
    parity = parity_of(result)
    dozen = dozen_of(result)
    column = column_of(result)
    half = half_of(result)

    total_win = 0.0
    results = []
    for bet in bets:
        kind = bet.get('type')
        value = bet.get('value')
        amount = float(bet.get('amount', 0))
        win = 0.0
        won = False

        if kind == 'straight':
            if value == result:
                win = amount * (PAYOUTS['straight'] + 1)  # return stake + winnings
                won = True
        elif kind in ('red','black'):
            if color == kind:
                win = amount * (PAYOUTS[kind] + 1)
                won = True
        elif kind in ('even','odd'):
            if parity == kind:
                win = amount * (PAYOUTS[kind] + 1)
                won = True
        elif kind in ('1st12','2nd12','3rd12'):
            if dozen == kind:
                win = amount * (PAYOUTS[kind] + 1)
                won = True
        elif kind in ('col1','col2','col3'):
            if column == kind:
                win = amount * (PAYOUTS[kind] + 1)
                won = True
        elif kind in ('1to18','19to36'):
            if half == kind:
                win = amount * (PAYOUTS[kind] + 1)
                won = True

        total_win += win
        results.append({'bet': bet, 'won': won, 'payout': win})

    return jsonify({
        'result': result,
        'color': color,
        'parity': parity,
        'dozen': dozen,
        'column': column,
        'half': half,
        'bets_result': results,
        'total_win': total_win
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
