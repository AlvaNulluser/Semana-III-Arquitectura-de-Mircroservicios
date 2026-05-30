document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const fileInput = document.getElementById('file-input');
    const chatContainer = document.getElementById('chat-container');
    const themeSelector = document.getElementById('theme');
    const providerSelector = document.getElementById('provider');
    const tokenInfo = document.getElementById('token-info');

    // Configuración de Marked (opcional: sanitización o manejo de enlaces)
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });

    // Cargar preferencias
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme;
    themeSelector.value = savedTheme;

    // Cambiar tema
    themeSelector.addEventListener('change', (e) => {
        const theme = e.target.value;
        document.body.className = theme;
        localStorage.setItem('theme', theme);
    });

    // Enviar mensaje
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        const files = fileInput.files;
        const provider = providerSelector.value;

        if (!message && files.length === 0) return;

        // Mostrar mensaje del usuario inmediatamente
        addMessage(message, 'user', files);

        // Bloquear UI mientras carga
        const sendBtn = document.getElementById('send-btn');
        sendBtn.disabled = true;
        sendBtn.textContent = 'Pensando...';

        // Preparar FormData para envío multimodal
        const formData = new FormData();
        formData.append('message', message);
        formData.append('provider', provider);
        for (let file of files) {
            formData.append('files', file);
        }

        // Limpiar inputs
        messageInput.value = '';
        fileInput.value = '';

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error en el servidor');
            }

            const data = await response.json();

            // Mostrar respuesta del bot con Markdown
            addMessage(data.response, 'bot');

            // Mostrar metadatos de archivos procesados
            if (data.files && data.files.length > 0) {
                let fileMetadataStr = "**Archivos analizados:**\n";
                data.files.forEach(f => {
                    fileMetadataStr += `- \`${f.name}\` (${(f.size/1024).toFixed(1)} KB, ${f.type})\n`;
                });
                addMessage(fileMetadataStr, 'bot');
            }

            // Actualizar tokens
            updateTokenInfo(data.tokens);

        } catch (error) {
            console.error('Error:', error);
            addMessage(`❌ **Error:** ${error.message}`, 'bot');
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Enviar';
        }
    });

    function addMessage(text, sender, files = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        // Renderizar Markdown
        messageDiv.innerHTML = marked.parse(text);

        // Aplicar resaltado de código post-render
        messageDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // Si el usuario subió archivos, mostrar mini-info visual
        if (files && files.length > 0) {
            const fileBadge = document.createElement('div');
            fileBadge.style.fontSize = '0.75rem';
            fileBadge.style.marginTop = '5px';
            fileBadge.style.opacity = '0.8';
            fileBadge.innerHTML = `📎 ${files.length} archivo(s) adjunto(s)`;
            messageDiv.appendChild(fileBadge);
        }
    }

    function updateTokenInfo(tokens) {
        tokenInfo.innerHTML = `
            <strong>Tokens:</strong> 
            Input: <span style="color:var(--accent-color)">${tokens.input}</span> | 
            Output: <span style="color:var(--accent-color)">${tokens.output}</span> | 
            Total: <strong>${tokens.total}</strong>
        `;
    }
});
