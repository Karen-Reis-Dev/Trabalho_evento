// URL da API
const API_URL = '/api';

// Função para carregar participantes
async function carregarParticipantes() {
    try {
        const response = await fetch(`${API_URL}/participantes`);
        const data = await response.json();
        
        // Atualizar contadores
        document.getElementById('vagasDisponiveis').textContent = data.vagas_disponiveis;
        document.getElementById('listaEsperaCount').textContent = data.total_espera;
        document.getElementById('confirmadosCount').textContent = `${data.total_confirmados}/${data.vagas_totais}`;
        document.getElementById('esperaCount').textContent = data.total_espera;
        
        // Atualizar lista de confirmados
        const listaConfirmadosDiv = document.getElementById('listaConfirmados');
        if (data.confirmados.length === 0) {
            listaConfirmadosDiv.innerHTML = '<div class="vazio">Nenhum participante confirmado ainda</div>';
        } else {
            listaConfirmadosDiv.innerHTML = data.confirmados.map(p => `
                <div class="card">
                    <p><strong>🎫 ${p.id}</strong></p>
                    <p><strong>Nome:</strong> ${p.nome}</p>
                    <p><strong>E-mail:</strong> ${p.email}</p>
                    <p><strong>Evento:</strong> ${p.evento_nome}</p>
                    <div class="numero-inscricao">Inscrito em: ${new Date(p.data_inscricao).toLocaleDateString('pt-BR')}</div>
                </div>
            `).join('');
        }
        
        // Atualizar lista de espera
        const listaEsperaDiv = document.getElementById('listaEspera');
        if (data.lista_espera.length === 0) {
            listaEsperaDiv.innerHTML = '<div class="vazio">Nenhum participante na lista de espera</div>';
        } else {
            listaEsperaDiv.innerHTML = data.lista_espera.map((p, index) => `
                <div class="card">
                    <p><strong>Posição:</strong> ${index + 1}° na fila</p>
                    <p><strong>Nome:</strong> ${p.nome}</p>
                    <p><strong>E-mail:</strong> ${p.email}</p>
                    <p><strong>Evento:</strong> ${p.evento_nome}</p>
                    <div class="numero-inscricao">Solicitado em: ${new Date(p.data_solicitacao).toLocaleDateString('pt-BR')}</div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Erro ao carregar participantes:', error);
    }
}

// Função para exibir confirmação
function exibirConfirmacao(participante, status, posicao = null) {
    if (status === 'confirmado') {
        document.getElementById('numInscricao').textContent = participante.id;
        const statusMsg = document.getElementById('statusMsg');
        statusMsg.textContent = `✅ Status: Inscrição confirmada! Número: ${participante.id}`;
        statusMsg.className = 'status confirmado';
    } else {
        document.getElementById('numInscricao').textContent = 'Aguardando...';
        const statusMsg = document.getElementById('statusMsg');
        statusMsg.textContent = `⏳ Status: Em lista de espera (Posição ${posicao}°)`;
        statusMsg.className = 'status espera';
    }
    
    document.getElementById('confNome').textContent = participante.nome;
    document.getElementById('confEmail').textContent = participante.email;
    document.getElementById('confTelefone').textContent = participante.telefone;
    document.getElementById('confEvento').textContent = participante.evento;
}

// Evento de submissão do formulário
document.getElementById('formInscricao').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const nome = document.getElementById('nome').value.trim();
    const email = document.getElementById('email').value.trim();
    const telefone = document.getElementById('telefone').value.trim();
    const evento = document.getElementById('evento').value;
    
    if (!nome || !email || !telefone || !evento) {
        alert('Por favor, preencha todos os campos!');
        return;
    }
    
    const btn = document.getElementById('btnInscricao');
    btn.disabled = true;
    btn.textContent = 'Processando...';
    
    try {
        const response = await fetch(`${API_URL}/inscricao`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nome, email, telefone, evento })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            exibirConfirmacao(result.participante, result.status, result.posicao);
            alert(result.status === 'confirmado' 
                ? `✅ Inscrição confirmada! Seu número é: ${result.participante.id}` 
                : `⏳ Vagas esgotadas! Você foi adicionado à lista de espera na posição ${result.posicao}.`);
            
            // Limpar formulário
            document.getElementById('nome').value = '';
            document.getElementById('email').value = '';
            document.getElementById('telefone').value = '';
            document.getElementById('evento').value = '';
            
            // Recarregar lista de participantes
            await carregarParticipantes();
            
            // Scroll para confirmação
            document.getElementById('confirmacao').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('Erro: ' + result.erro);
        }
    } catch (error) {
        console.error('Erro ao realizar inscrição:', error);
        alert('Erro ao conectar com o servidor. Tente novamente.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Realizar Inscrição';
    }
});

// Carregar participantes ao iniciar
carregarParticipantes();

// Atualizar a cada 30 segundos
setInterval(carregarParticipantes, 30000);

// Habilitar/desabilitar botão baseado no formulário
const inputs = ['nome', 'email', 'telefone', 'evento'];
function toggleButton() {
    const nome = document.getElementById('nome').value;
    const email = document.getElementById('email').value;
    const telefone = document.getElementById('telefone').value;
    const evento = document.getElementById('evento').value;
    document.getElementById('btnInscricao').disabled = !(nome && email && telefone && evento);
}

inputs.forEach(id => {
    document.getElementById(id).addEventListener('input', toggleButton);
});