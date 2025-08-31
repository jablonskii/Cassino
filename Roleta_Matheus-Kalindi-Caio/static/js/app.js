document.addEventListener('DOMContentLoaded', () => {
    const spinBtn = document.getElementById('spinBtn');
    const animationContainer = document.getElementById('animation-container');
    const lastResultEl = document.getElementById('lastResult');
    const bankrollEl = document.getElementById('bankroll');
    const chipValueInput = document.getElementById('chipValue');
    const betsTableBody = document.getElementById('betsTable');
    const clearBetsBtn = document.getElementById('clearBets');
    const betButtons = document.querySelectorAll('.bet');

    let bankroll = parseFloat(bankrollEl.textContent);
    let bets = [];
    let isSpinning = false; 

    const animationImages = [
        '/static/images/vermelho.png',
        '/static/images/preto.png',
        '/static/images/verde.png'
    ];
    const animationDuration = 3000; 
    const animationIntervalSpeed = 200; 
    let animationInterval;

    function renderBets() {
        betsTableBody.innerHTML = ''; 

        if (bets.length === 0) {
            betsTableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color: var(--muted);">Nenhuma aposta feita</td></tr>';
            return;
        }

        bets.forEach((bet, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${bet.type}</td>
                <td>${bet.value || '—'}</td>
                <td>R$ ${bet.amount.toFixed(2)}</td>
                <td><button class="btn-remove" data-index="${index}" style="background: #c62828; color: white; border: none; border-radius: 4px; cursor: pointer; width: 20px; height: 20px;">X</button></td>
            `;
            betsTableBody.appendChild(row);
        });
    }
    
    function placeBet(e) {
        if (isSpinning) return;

        const target = e.currentTarget;
        const type = target.dataset.type;
        const value = target.dataset.value || null;
        const amount = parseFloat(chipValueInput.value);

        if (isNaN(amount) || amount <= 0) {
            alert('Por favor, insira um valor de ficha válido.');
            return;
        }

        if (amount > bankroll) {
            alert('Saldo insuficiente para fazer esta aposta.');
            return;
        }

        bankroll -= amount;
        bankrollEl.textContent = bankroll.toFixed(2);

        bets.push({ type, value, amount });
        renderBets();
    }

    function removeBet(e) {
        if (e.target.classList.contains('btn-remove')) {
            const indexToRemove = parseInt(e.target.dataset.index, 10);
            const betToRemove = bets[indexToRemove];

            bankroll += betToRemove.amount;
            bankrollEl.textContent = bankroll.toFixed(2);

            bets.splice(indexToRemove, 1);
            renderBets();
        }
    }

    function clearAllBets() {
        const totalBetAmount = bets.reduce((sum, bet) => sum + bet.amount, 0);
        bankroll += totalBetAmount;
        bankrollEl.textContent = bankroll.toFixed(2);

        bets = [];
        renderBets();
    }

    function startAnimation() {
        let imageIndex = 0;
        animationContainer.innerHTML = '';

        const img = document.createElement('img');
        img.className = 'wheel-img';
        animationContainer.appendChild(img);

        animationInterval = setInterval(() => {
            img.src = animationImages[imageIndex];
            imageIndex = (imageIndex + 1) % animationImages.length;
        }, animationIntervalSpeed);
    }

    function showResult(apiData) {
        clearInterval(animationInterval);

        const resultNumber = apiData.result;
        const resultColor = apiData.color;
        
        const resultImageUrl = `/static/images/${resultNumber}.png`;
        
        animationContainer.innerHTML = `<img src="${resultImageUrl}" alt="Resultado ${resultNumber}" class="wheel-img">`;
        
        if(lastResultEl) {
            lastResultEl.textContent = `Último resultado: ${resultNumber} (${resultColor})`;
        }
        
        bankroll = parseFloat(apiData.new_bankroll);
        bankrollEl.textContent = bankroll.toFixed(2);

        bets = [];
        renderBets();
    }

    async function handleSpin() {
        if (bets.length === 0) {
            alert('Você precisa fazer pelo menos uma aposta para girar a roleta.');
            return;
        }
        if (isSpinning) return;

        isSpinning = true;
        spinBtn.disabled = true;
        spinBtn.textContent = 'A girar...';
        
        startAnimation();

        setTimeout(async () => {
            try {
                const response = await fetch('/spin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ bets })
                });

                if (!response.ok) {
                    throw new Error(`Erro na comunicação com o servidor: ${response.statusText}`);
                }

                const data = await response.json();
                showResult(data);

            } catch (error) {
                console.error('Falha ao girar:', error);
                if (lastResultEl) {
                    lastResultEl.textContent = 'Erro ao girar. Tente novamente.';
                }
                animationContainer.innerHTML = `<img src="/static/images/roleta.png" alt="Roleta Americana" class="wheel-img">`;
                clearAllBets();
            } finally {
                isSpinning = false;
                spinBtn.disabled = false;
                spinBtn.textContent = 'Girar';
            }
        }, animationDuration);
    }

    spinBtn.addEventListener('click', handleSpin);
    clearBetsBtn.addEventListener('click', clearAllBets);
    
    betButtons.forEach(button => {
        button.addEventListener('click', placeBet);
    });

    betsTableBody.addEventListener('click', removeBet);

    renderBets(); 
});

