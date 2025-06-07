document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startButton');
    const volumeBar = document.getElementById('volumeBar');
    const statusMessage = document.getElementById('statusMessage');

    let audioContext;
    let analyser;
    let microphone;
    let javascriptNode; // For ScriptProcessorNode, deprecated but widely supported for this use case
    let dataArray;

    const REQUESTING_PERMISSION = "Solicitando permissão...";
    const PERMISSION_GRANTED = "Permissão concedida. Capturando áudio...";
    const PERMISSION_DENIED = "Permissão de microfone negada.";
    const CAPTURE_ENDED = "Captura de áudio encerrada.";
    const ERROR_GENERAL = "Erro ao acessar o microfone: ";
    const ERROR_UNSUPPORTED = "Web Audio API não é suportada neste navegador.";

    function updateVolumeMeter() {
        if (!analyser) return;

        analyser.getByteFrequencyData(dataArray); // ou getByteTimeDomainData

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const average = sum / dataArray.length;

        // Normaliza e converte para porcentagem (0 a 100)
        // O valor de 'average' pode variar, ajuste o fator de escala se necessário.
        // Para getByteFrequencyData, os valores são de 0 a 255.
        const volumePercentage = Math.min(100, Math.max(0, (average / 255) * 250)); // Multiplicador para sensibilidade
        volumeBar.style.width = volumePercentage + '%';

        // Solicita o próximo quadro de animação para continuar atualizando
        requestAnimationFrame(updateVolumeMeter);
    }

    async function startAudioCapture() {
        startButton.disabled = true;
        statusMessage.textContent = REQUESTING_PERMISSION;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            statusMessage.textContent = ERROR_UNSUPPORTED;
            console.error(ERROR_UNSUPPORTED);
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });

            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            microphone = audioContext.createMediaStreamSource(stream);

            // Configurar o AnalyserNode
            analyser.fftSize = 256; // Tamanho da FFT, influencia a quantidade de dados de frequência
            const bufferLength = analyser.frequencyBinCount; // Metade do fftSize
            dataArray = new Uint8Array(bufferLength);

            // Conectar os nós: microfone -> analisador
            microphone.connect(analyser);

            // ScriptProcessorNode (alternativa para navegadores mais antigos ou para processamento mais direto)
            // Nota: ScriptProcessorNode é obsoleto, AudioWorklet é o sucessor moderno,
            // mas para um simples medidor de volume, ScriptProcessor ainda funciona e é mais simples para protótipos.
            // Se não precisarmos processar os buffers de áudio diretamente (apenas analisar),
            // o AnalyserNode ligado a nada (ou a um gainNode e depois destination) é suficiente.
            // Para este exemplo, o AnalyserNode já faz o trabalho para o medidor de volume.

            statusMessage.textContent = PERMISSION_GRANTED;
            console.log("Captura de áudio iniciada.");

            // Inicia a atualização do medidor de volume
            updateVolumeMeter();

            // Opcional: parar a captura após um tempo ou com outro botão
            // Para este protótipo, a captura continua até a página ser fechada.
            // Para parar explicitamente:
            // stream.getTracks().forEach(track => track.stop());
            // audioContext.close();

        } catch (err) {
            statusMessage.textContent = PERMISSION_DENIED;
            if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                statusMessage.textContent = PERMISSION_DENIED;
                console.error(PERMISSION_DENIED, err);
            } else {
                statusMessage.textContent = ERROR_GENERAL + err.message;
                console.error(ERROR_GENERAL, err);
            }
            startButton.disabled = false; // Reabilita o botão se houver erro
        }
    }

    startButton.addEventListener('click', startAudioCapture);

    // Limpeza ao fechar a página (nem sempre garantido, mas boa prática)
    window.addEventListener('beforeunload', () => {
        if (audioContext && audioContext.state !== 'closed') {
            // Parar tracks do microfone
            if (microphone && microphone.mediaStream) {
                microphone.mediaStream.getTracks().forEach(track => track.stop());
            }
            audioContext.close();
            console.log(CAPTURE_ENDED);
        }
    });
});
