document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('settings-form');
    const modal = document.getElementById('response-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const modalClose = document.getElementById('modal-close');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    // Status elements
    const obsStatus = document.getElementById('obs-status');
    const lastRecording = document.getElementById('last-recording');
    const latestFiles = document.getElementById('latest-files');
    const archivedFiles = document.getElementById('archived-files');

    // Action buttons
    const testConnectionBtn = document.getElementById('test-connection');
    const manualRecordingBtn = document.getElementById('manual-recording');
    const viewLatestBtn = document.getElementById('view-latest');
    const clearOldBtn = document.getElementById('clear-old');
    const refreshStatusBtn = document.getElementById('refresh-status');

    // Show modal function
    function showModal(title, message, isError = false) {
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        modalMessage.style.color = isError ? '#ef4444' : '#10b981';
        modal.style.display = 'block';
    }

    // Close modal
    function closeModal() {
        modal.style.display = 'none';
    }

    modalClose.addEventListener('click', closeModal);
    modalCloseBtn.addEventListener('click', closeModal);

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Load current settings
    async function loadSettings() {
        try {
            const response = await fetch('/api/settings');
            if (!response.ok) throw new Error('Falha ao carregar configurações');
            
            const settings = await response.json();
            
            // Populate form fields
            document.getElementById('obs_host').value = settings.obs_host;
            document.getElementById('obs_port').value = settings.obs_port;
            document.getElementById('obs_password').value = settings.obs_password;
            document.getElementById('standby_delay').value = settings.standby_delay;
            document.getElementById('recording_duration').value = settings.recording_duration;

        } catch (error) {
            showModal('Erro', `Erro ao carregar configurações: ${error.message}`, true);
        }
    }

    // Load system status
    async function loadSystemStatus() {
        try {
            // Load video files count
            const latestResponse = await fetch('/api/videos/old');
            if (latestResponse.ok) {
                const data = await latestResponse.json();
                archivedFiles.textContent = data.videos.length;
            }

            // Check for latest video
            const latestVideoResponse = await fetch('/api/videos/latest');
            if (latestVideoResponse.ok) {
                const blob = await latestVideoResponse.blob();
                if (blob.size > 0) {
                    latestFiles.textContent = '1';
                    lastRecording.textContent = 'Disponível';
                } else {
                    latestFiles.textContent = '0';
                    lastRecording.textContent = 'Nenhum';
                }
            } else {
                latestFiles.textContent = '0';
                lastRecording.textContent = 'Nenhum';
            }

            // OBS status (simplified check)
            obsStatus.textContent = 'Verificar conexão';

        } catch (error) {
            console.error('Erro ao carregar status:', error);
        }
    }

    // Handle form submission
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const newSettings = Object.fromEntries(formData.entries());

        // Convert numbers
        newSettings.obs_port = parseInt(newSettings.obs_port, 10);
        newSettings.standby_delay = parseInt(newSettings.standby_delay, 10);
        newSettings.recording_duration = parseInt(newSettings.recording_duration, 10);

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newSettings),
            });

            const result = await response.json();

            if (response.ok) {
                showModal('Sucesso', result.message || 'Configurações salvas com sucesso!');
            } else {
                throw new Error(result.detail || 'Falha ao salvar configurações');
            }
        } catch (error) {
            showModal('Erro', `Erro ao salvar configurações: ${error.message}`, true);
        }
    });

    // Test OBS connection
    testConnectionBtn.addEventListener('click', async () => {
        testConnectionBtn.disabled = true;
        testConnectionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testando...';

        try {
            // Try to start a recording to test connection
            const response = await fetch('/api/recording/start', {
                method: 'POST',
            });

            if (response.status === 202) {
                obsStatus.textContent = 'Conectado';
                obsStatus.style.color = '#10b981';
                showModal('Sucesso', 'Conexão com OBS estabelecida com sucesso!');
            } else {
                throw new Error('Falha na conexão');
            }
        } catch (error) {
            obsStatus.textContent = 'Erro de conexão';
            obsStatus.style.color = '#ef4444';
            showModal('Erro', 'Não foi possível conectar ao OBS. Verifique as configurações.', true);
        } finally {
            testConnectionBtn.disabled = false;
            testConnectionBtn.innerHTML = '<i class="fas fa-plug"></i> Testar Conexão OBS';
        }
    });

    // Manual recording
    manualRecordingBtn.addEventListener('click', async () => {
        if (!confirm('Deseja iniciar uma gravação manual?')) return;

        manualRecordingBtn.disabled = true;
        manualRecordingBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gravando...';

        try {
            const response = await fetch('/api/recording/start', {
                method: 'POST',
            });

            if (response.status === 202) {
                showModal('Sucesso', 'Gravação manual iniciada com sucesso!');
                // Refresh status after a delay
                setTimeout(() => {
                    loadSystemStatus();
                }, 20000);
            } else {
                throw new Error('Falha ao iniciar gravação');
            }
        } catch (error) {
            showModal('Erro', `Erro ao iniciar gravação: ${error.message}`, true);
        } finally {
            manualRecordingBtn.disabled = false;
            manualRecordingBtn.innerHTML = '<i class="fas fa-play-circle"></i> Iniciar Gravação Manual';
        }
    });

    // View latest video
    viewLatestBtn.addEventListener('click', () => {
        window.open('/api/videos/latest', '_blank');
    });

    // Clear old videos
    clearOldBtn.addEventListener('click', () => {
        if (confirm('Deseja limpar todos os arquivos antigos? Esta ação não pode ser desfeita.')) {
            showModal('Informação', 'Funcionalidade de limpeza ainda não implementada.', true);
        }
    });

    // Refresh status
    refreshStatusBtn.addEventListener('click', () => {
        refreshStatusBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        loadSystemStatus().then(() => {
            refreshStatusBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar Status';
            showModal('Sucesso', 'Status do sistema atualizado!');
        });
    });

    // Initial load
    loadSettings();
    loadSystemStatus();
});
