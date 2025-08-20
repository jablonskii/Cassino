
const bankrollEl = document.getElementById('bankroll');
const chipEl = document.getElementById('chipValue');
const betsTable = document.getElementById('betsTable');
const lastResult = document.getElementById('lastResult');
const spinBtn = document.getElementById('spinBtn');
const clearBtn = document.getElementById('clearBets');

let bankroll = 1000;
let bets = [];

function renderBets(){
  betsTable.innerHTML = '';
  bets.forEach((b, i) => {
    const tr = document.createElement('tr');
    const label = b.type === 'straight' ? `${b.type}(${b.value})` : b.type;
    tr.innerHTML = `<td>${label}</td><td>${b.value ?? '-'}</td><td>${b.amount.toFixed(2)}</td>
                    <td><button data-i="${i}" class="btn-outline small">remover</button></td>`;
    betsTable.appendChild(tr);
  });
  betsTable.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.i);
      bankroll += bets[i].amount;
      bets.splice(i,1);
      bankrollEl.textContent = bankroll.toFixed(2);
      renderBets();
    });
  });
}

function addBet(type, value){
  const amount = Math.max(1, parseFloat(chipEl.value || '10'));
  if (bankroll < amount){ alert('Saldo insuficiente'); return; }
  bankroll -= amount;
  bankrollEl.textContent = bankroll.toFixed(2);
  bets.push({type, value, amount});
  renderBets();
}

document.querySelectorAll('.bet').forEach(btn => {
  btn.addEventListener('click', () => {
    const type = btn.dataset.type;
    const value = btn.dataset.value ? (btn.dataset.value === '00' ? '00' : parseInt(btn.dataset.value)) : null;
    addBet(type, value);
  });
});

clearBtn.addEventListener('click', () => {
  // refund all
  bets.forEach(b => bankroll += b.amount);
  bets = [];
  bankrollEl.textContent = bankroll.toFixed(2);
  renderBets();
});

async function spin(){
  spinBtn.disabled = true; spinBtn.textContent = 'Girando...';
  try{
    const res = await fetch('/spin', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({bets})
    });
    const data = await res.json();
    const r = data.result;
    const col = data.color;
    lastResult.textContent = `Último resultado: ${r} (${col})`;

    // pagamentos já vieram calculados em data.bets_result / total_win
    const total = data.total_win || 0;
    bankroll += total;
    bankrollEl.textContent = bankroll.toFixed(2);
    // limpar apostas usadas
    bets = [];
    renderBets();
  } catch(e){
    alert('Falha ao girar: ' + e);
  } finally{
    spinBtn.disabled = false; spinBtn.textContent = 'Girar';
  }
}

spinBtn.addEventListener('click', spin);
renderBets();
