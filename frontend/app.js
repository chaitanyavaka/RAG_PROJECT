// App Logic

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const traceContainer = document.getElementById('mcp-trace');
    const traceLogs = document.getElementById('trace-logs');

    // State
    let isProcessing = false;

    // --- Chat Functions ---

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query || isProcessing) return;

        addMessage(query, 'user');
        userInput.value = '';

        isProcessing = true;
        showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            if (!response.ok) throw new Error('API Error');

            const data = await response.json();
            removeTypingIndicator();

            addMessage(data.answer, 'bot', data.context);
            logTrace(data.trace_id, "Completed", "Chat Request");
        } catch (error) {
            removeTypingIndicator();
            addMessage("Sorry, I encountered an error processing your request.", 'bot');
            showToast("Error connecting to server", "error");
        } finally {
            isProcessing = false;
        }
    });

    function addMessage(text, sender, context = null) {
        // Clear welcome if present
        if (chatMessages.querySelector('.flex-col.items-center')) {
            chatMessages.innerHTML = '';
        }

        const div = document.createElement('div');
        div.className = `flex w-full mb-4 message-enter ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

        const bubble = document.createElement('div');
        bubble.className = `max-w-[80%] rounded-2xl p-4 shadow-md text-sm leading-relaxed ${sender === 'user'
                ? 'bg-gradient-to-br from-primary to-secondary text-white rounded-tr-none'
                : 'bg-white/10 text-gray-200 border border-white/5 rounded-tl-none'
            }`;

        // Markdown-ish parsing (basic)
        const formatText = (str) => {
            return str
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
        };

        bubble.innerHTML = formatText(text);

        if (context) {
            const details = document.createElement('details');
            details.className = "mt-2 text-xs text-gray-400 cursor-pointer pt-2 border-t border-white/10";
            details.innerHTML = `
                <summary class="hover:text-primary transition-colors select-none">View Sources</summary>
                <div class="mt-2 p-2 bg-black/20 rounded font-mono whitespace-pre-wrap">${context}</div>
            `;
            bubble.appendChild(details);
        }

        div.appendChild(bubble);
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    let typingDiv = null;

    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = `flex w-full mb-4 message-enter justify-start`;
        div.innerHTML = `
            <div class="bg-white/5 rounded-2xl rounded-tl-none p-4 flex gap-1 items-center">
                <div class="typing-dot bg-gray-400"></div>
                <div class="typing-dot bg-gray-400"></div>
                <div class="typing-dot bg-gray-400"></div>
            </div>
        `;
        typingDiv = div;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        if (typingDiv) typingDiv.remove();
        typingDiv = null;
    }

    // --- File Upload Functions ---

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-primary', 'bg-primary/5');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary', 'bg-primary/5');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-primary', 'bg-primary/5');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    async function handleFiles(files) {
        for (const file of files) {
            await uploadFile(file);
        }
    }

    async function uploadFile(file) {
        const id = Math.random().toString(36).substr(2, 9);
        addFileItem(file.name, id, 'uploading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            updateFileStatus(id, 'done');
            showToast(`Uploaded ${file.name}`, 'success');

            // Log MCP Trace
            if (data.result && data.result.trace_id) {
                logTrace(data.result.trace_id, "Ingestion Complete", `Uploaded ${file.name}`);
            }

        } catch (error) {
            updateFileStatus(id, 'error');
            showToast(`Failed to upload ${file.name}`, 'error');
        }
    }

    function addFileItem(name, id, status) {
        const div = document.createElement('div');
        div.id = `file-${id}`;
        div.className = "flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5 text-sm hover:bg-white/10 transition-colors";
        div.innerHTML = `
            <div class="flex items-center gap-2 truncate">
                <i data-lucide="file-text" class="w-4 h-4 text-gray-400"></i>
                <span class="truncate max-w-[120px] text-gray-300">${name}</span>
            </div>
            <div class="status-icon">
                ${status === 'uploading' ? '<i data-lucide="loader-2" class="w-4 h-4 text-blue-400 animate-spin"></i>' : ''}
            </div>
        `;
        fileList.appendChild(div);
        lucide.createIcons();
    }

    function updateFileStatus(id, status) {
        const el = document.getElementById(`file-${id}`);
        if (!el) return;
        const iconContainer = el.querySelector('.status-icon');

        if (status === 'done') {
            iconContainer.innerHTML = '<i data-lucide="check-circle" class="w-4 h-4 text-emerald-500"></i>';
        } else if (status === 'error') {
            iconContainer.innerHTML = '<i data-lucide="alert-circle" class="w-4 h-4 text-red-500"></i>';
        }
        lucide.createIcons();
    }

    // --- MCP Trace ---

    // Simulate real-time trace updates or just list completed ones for now
    function logTrace(traceId, status, info) {
        const div = document.createElement('div');
        div.className = "p-2 bg-white/5 rounded border-l-2 border-primary";
        div.innerHTML = `
            <div class="flex justify-between opacity-50 mb-1">
                <span>${traceId.substr(0, 8)}...</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="font-bold text-white">${status}</div>
            <div class="truncate opacity-75">${info}</div>
        `;
        traceLogs.prepend(div);

        // Show panel briefly
        traceContainer.classList.remove('translate-x-full');
        setTimeout(() => traceContainer.classList.add('translate-x-full'), 5000);
    }

    document.getElementById('close-trace').addEventListener('click', () => {
        traceContainer.classList.add('translate-x-full');
    });

    // --- Toast ---

    function showToast(msg, type = 'info') {
        const div = document.createElement('div');
        div.className = `px-4 py-3 rounded-xl shadow-xl text-sm font-medium flex items-center gap-2 message-enter pointer-events-auto ${type === 'success' ? 'bg-emerald-500/90 text-white' :
                type === 'error' ? 'bg-red-500/90 text-white' :
                    'bg-gray-800 text-white border border-white/20'
            }`;
        div.innerHTML = msg;
        const container = document.getElementById('toast-container');
        container.appendChild(div);
        setTimeout(() => div.remove(), 3000);
    }

});
