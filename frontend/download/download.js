document.addEventListener('DOMContentLoaded', () => {
    // Elementos da página
    const videoPlaceholder = document.getElementById('video-placeholder');
    const videoInfo = document.getElementById('video-info');
    const videoTitle = document.getElementById('video-title');
    const videoDate = document.getElementById('video-date');
    const videoSize = document.getElementById('video-size');
    const downloadLatest = document.getElementById('download-latest');
    const playVideo = document.getElementById('play-video');
    const noVideoMessage = document.getElementById('no-video-message');
    const archivedGrid = document.getElementById('archived-grid');
    const noArchivedMessage = document.getElementById('no-archived-message');
    
    // Modal elements
    const videoModal = document.getElementById('video-modal');
    const videoPlayer = document.getElementById('video-player');
    const videoModalClose = document.getElementById('video-modal-close');

    let currentVideoUrl = null;
    let currentVideoName = null;

    // Função para formatar tamanho do arquivo
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Função para formatar data
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async function fetchLatestVideo() {
        try {
            const response = await fetch('/api/videos/latest');

            if (response.ok) {
                const videoUrl = response.url;
                currentVideoUrl = videoUrl;

                let videoName = 'video-recording.mp4';
                const contentDisposition = response.headers.get('content-disposition');
                if (contentDisposition) {
                    const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                    if (filenameMatch && filenameMatch[1]) {
                        videoName = filenameMatch[1].replace(/['"]/g, '');
                    }
                }
                currentVideoName = videoName;

                const lastModified = response.headers.get('last-modified');
                const contentLength = response.headers.get('content-length');
                const formattedDate = lastModified ? formatDate(lastModified) : 'Data não disponível';
                const formattedSize = contentLength ? formatFileSize(parseInt(contentLength, 10)) : 'Tamanho não disponível';

                videoPlaceholder.style.display = 'none';
                noVideoMessage.style.display = 'none';
                videoInfo.style.display = 'flex';
                videoTitle.textContent = 'Vídeo Disponível';
                videoDate.textContent = `Data: ${formattedDate}`;
                videoSize.textContent = `Tamanho: ${formattedSize}`;

                downloadLatest.href = videoUrl;
                downloadLatest.download = videoName;
            } else {
                showNoVideo();
            }
        } catch (error) {
            console.error('Erro ao buscar vídeo mais recente:', error);
            showNoVideo();
        }
    }

    function showNoVideo() {
        videoPlaceholder.style.display = 'flex';
        videoInfo.style.display = 'none';
        noVideoMessage.style.display = 'block';
        currentVideoUrl = null;
        currentVideoName = null;
    }

    // Buscar vídeos arquivados
    async function fetchArchivedVideos() {
        try {
            const response = await fetch('/api/videos/old');
            const data = await response.json();
            
            archivedGrid.innerHTML = ''; // Limpar grid
            
            if (data.videos && data.videos.length > 0) {
                noArchivedMessage.style.display = 'none';
                
                data.videos.forEach(videoName => {
                    const videoItem = document.createElement('div');
                    videoItem.className = 'archived-item';
                    
                    videoItem.innerHTML = `
                        <div class="archived-item-header">
                            <i class="fas fa-file-video"></i>
                            <span>${videoName}</span>
                        </div>
                        <div class="archived-item-content">
                            <p>Vídeo arquivado</p>
                            <a href="/videos/old/${videoName}" class="download-link" download>
                                <i class="fas fa-download"></i>
                                Baixar
                            </a>
                        </div>
                    `;
                    
                    archivedGrid.appendChild(videoItem);
                });
            } else {
                noArchivedMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Erro ao buscar vídeos arquivados:', error);
            noArchivedMessage.style.display = 'block';
        }
    }

    // Event listeners
    playVideo.addEventListener('click', () => {
        if (currentVideoUrl) {
            videoPlayer.src = currentVideoUrl;
            videoModal.style.display = 'block';
        }
    });

    videoModalClose.addEventListener('click', () => {
        videoModal.style.display = 'none';
        videoPlayer.pause();
    });

    window.addEventListener('click', (event) => {
        if (event.target === videoModal) {
            videoModal.style.display = 'none';
            videoPlayer.pause();
        }
    });

    // Função para atualizar automaticamente quando novos vídeos estiverem disponíveis
    function setupAutoRefresh() {
        // Verificar por novos vídeos a cada 30 segundos
        setInterval(async () => {
            try {
                const response = await fetch('/api/videos/latest');
                if (response.ok) {
                    const blob = await response.blob();
                    if (blob.size > 0 && !currentVideoUrl) {
                        // Novo vídeo disponível!
                        console.log('Novo vídeo detectado, atualizando página...');
                        fetchLatestVideo();
                        fetchArchivedVideos();
                    }
                }
            } catch (error) {
                console.error('Erro ao verificar novos vídeos:', error);
            }
        }, 30000); // Verificar a cada 30 segundos
    }

    // Inicializar página
    fetchLatestVideo();
    fetchArchivedVideos();
    setupAutoRefresh();
});
