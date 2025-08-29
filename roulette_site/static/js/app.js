// Aguarda o carregamento completo do DOM antes de executar o script
document.addEventListener('DOMContentLoaded', () => {

    // ==============================================
    // SELEÇÃO DE ELEMENTOS DO DOM
    // ==============================================
    const spinBtn = document.getElementById('spinBtn');
    const animationContainer = document.getElementById('animation-container');
    const lastResultEl = document.getElementById('lastResult');
    const bankrollEl = document.getElementById('bankroll');
    const chipValueInput = document.getElementById('chipValue');
    const betsTableBody = document.getElementById('betsTable');
    const clearBetsBtn = document.getElementById('clearBets');
    const betButtons = document.querySelectorAll('.bet');
    

    // ==============================================
    // ESTADO DO JOGO
    // ==============================================
    let bankroll = parseFloat(bankrollEl.textContent);
    let bets = []; // Array para armazenar as apostas da rodada atual
    let isSpinning = false; // Flag para evitar múltiplos cliques durante o giro

    // ==============================================
    // CONFIGURAÇÕES DA ANIMAÇÃO
    // ==============================================
    const animationImages = [
        '/static/images/vermelho.png',
        '/static/images/preto.png',
        '/static/images/verde.png'
    ];
    const animationDuration = 3000; // 3 segundos
    const animationIntervalSpeed = 100; // Troca de imagem a cada 100ms
    let animationInterval;

    // ==============================================
    // FUNÇÕES PRINCIPAIS
    // ==============================================

    /**
     * Renderiza a tabela de apostas atuais com base no array `bets`.
     */
    function renderBets() {
        betsTableBody.innerHTML = ''; // Limpa a tabela antes de renderizar

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
    
    /**
     * Adiciona uma nova aposta ao array `bets` e desconta do saldo.
     * @param {Event} e - O evento de clique do botão de aposta.
     */
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

    /**
     * Remove uma aposta do array `bets` e reembolsa o saldo.
     * @param {Event} e - O evento de clique do botão de remover.
     */
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

    /**
     * Limpa todas as apostas atuais e reembolsa o saldo.
     */
    function clearAllBets() {
        const totalBetAmount = bets.reduce((sum, bet) => sum + bet.amount, 0);
        bankroll += totalBetAmount;
        bankrollEl.textContent = bankroll.toFixed(2);

        bets = [];
        renderBets();
    }

    /**
     * Inicia a animação de troca de imagens.
     */
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

    /**
     * Para a animação e exibe o resultado final.
     * @param {object} apiData - Os dados retornados pela API.
     */
    function showResult(apiData) {
        clearInterval(animationInterval);
        
        // MODIFICAÇÃO 2: Trata a resposta do servidor
        if (apiData.error) {
            alert(apiData.error);
            clearAllBets(); 
            return;
        }

        const resultNumber = apiData.result;
        const resultColor = apiData.color;
        
        
        animationContainer.innerHTML = `<img src="/static/images/${resultNumber}.png" ...>`;
        lastResultEl.textContent = `Último resultado: ${resultNumber} (${resultColor})`;

        // MODIFICAÇÃO 3: Atualiza o saldo com o valor exato vindo do servidor
        bankroll = parseFloat(apiData.new_bankroll);
        bankrollEl.textContent = bankroll.toFixed(2);

        // Limpa as apostas para a próxima rodada
        bets = [];
        renderBets();
    }

    /**
     * Orquestra todo o processo de giro.
     */
    async function handleSpin() {
        if (bets.length === 0) {
            alert('Você precisa fazer pelo menos uma aposta para girar a roleta.');
            return;
        }
        if (isSpinning) return;

        isSpinning = true;
        spinBtn.disabled = true;
        spinBtn.textContent = 'Girando...';
        
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
                if(lastResultEl) {
                    lastResultEl.textContent = 'Erro ao girar. Tente novamente.';
                }
                animationContainer.innerHTML = `<img src="/static/images/roleta.png" alt="Roleta Americana" class="wheel-img">`;
                // Se houver erro, devolve o dinheiro das apostas
                clearAllBets();
            } finally {
                isSpinning = false;
                spinBtn.disabled = false;
                spinBtn.textContent = 'Girar';
            }
        }, animationDuration);
    }

    // ==============================================
    // EVENT LISTENERS
    // ==============================================
    spinBtn.addEventListener('click', handleSpin);
    clearBetsBtn.addEventListener('click', clearAllBets);
    
    betButtons.forEach(button => {
        button.addEventListener('click', placeBet);
    });

    betsTableBody.addEventListener('click', removeBet);

    // ==============================================
    // INICIALIZAÇÃO
    // ==============================================
    bankrollEl.textContent = bankroll.toFixed(2);
    renderBets();
});

document.addEventListener('DOMContentLoaded', () => {
    // Seleção de elementos... (o seu código existente)
    const bankrollEl = document.getElementById('bankroll');
    
    // MODIFICAÇÃO 1: Lê o saldo inicial do HTML, em vez de o definir como 1000
    let bankroll = parseFloat(bankrollEl.textContent.replace(',', '.'));
    let bets = [];
    // ... resto das suas variáveis

    // ... (as suas funções placeBet, removeBet, clearAllBets continuam iguais)
    
    function showResult(apiData) {
        clearInterval(animationInterval);
        
        // MODIFICAÇÃO 2: Trata a resposta do servidor
        if (apiData.error) {
            alert(apiData.error);
            clearAllBets(); 
            return;
        }

        const resultNumber = apiData.result;
        const resultColor = apiData.color;
        
        
        animationContainer.innerHTML = `<img src="/static/images/${resultNumber}.png" ...>`;
        lastResultEl.textContent = `Último resultado: ${resultNumber} (${resultColor})`;

        // MODIFICAÇÃO 3: Atualiza o saldo com o valor exato vindo do servidor
        bankroll = parseFloat(apiData.new_bankroll);
        bankrollEl.textContent = bankroll.toFixed(2);

        // Limpa as apostas para a próxima rodada
        bets = [];
        renderBets();
    }
    
    // ... (o resto do seu ficheiro JS continua igual)
});
