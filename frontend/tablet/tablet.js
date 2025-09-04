document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('start-button');
    const statusMessage = document.getElementById('status-message');
    const statusIndicator = document.getElementById('status-indicator');

    // Status messages in Portuguese
    const messages = {
        ready: 'Pronto para iniciar',
        recording: 'Gravando vídeo...',
        standby: 'Preparando câmera...',
        processing: 'Processando vídeo...',
        completed: 'Gravação concluída!',
        error: 'Erro na gravação',
        connectionError: 'Erro de conexão com o servidor'
    };

    function updateStatus(status, message) {
        statusMessage.textContent = message;
        statusIndicator.className = `status-indicator status-${status}`;
    }

    startButton.addEventListener('click', async () => {
        startButton.disabled = true;
        updateStatus('standby', messages.standby);

        try {
            // First, move the old video to the 'old' folder
            await fetch('/api/videos/move-to-old', {
                method: 'POST',
            });

            const response = await fetch('/api/recording/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.status === 202) {
                updateStatus('recording', messages.recording);
                
                // Simulate the recording process timing
                // Standby delay + recording duration + processing time
                const totalDelay = 3000 + 10000 + 2000; // 3s + 10s + 2s
                
                setTimeout(() => {
                    updateStatus('processing', messages.processing);
                }, 3000);
                
                setTimeout(() => {
                    updateStatus('completed', messages.completed);
                    startButton.disabled = false;
                    
                    // Return to ready state after showing completion
                    setTimeout(() => {
                        updateStatus('ready', messages.ready);
                    }, 3000);
                }, totalDelay);
                
            } else {
                const result = await response.json();
                updateStatus('error', `${messages.error}: ${result.detail || 'Erro desconhecido'}`);
                startButton.disabled = false;
            }
        } catch (error) {
            console.error('Erro ao iniciar gravação:', error);
            updateStatus('error', messages.connectionError);
            startButton.disabled = false;
        }
    });

    // Initialize status
    updateStatus('ready', messages.ready);
});
