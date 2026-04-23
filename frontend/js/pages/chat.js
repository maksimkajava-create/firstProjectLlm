import { api, toast } from '../api.js';

let messages = JSON.parse(localStorage.getItem('chatMessages') || '[]');
let polls = {};

function saveMessages() { localStorage.setItem('chatMessages', JSON.stringify(messages)); }

function renderMessages() {
    const box = document.getElementById('chat-box');
    if (!box) return;
    box.innerHTML = messages.length === 0
        ? '<div class="text-muted text-center mt-5">Отправьте первый запрос ↓</div>'
        : messages.map(m => {
            if (m.role === 'user') return `<div class="chat-msg user"><b>Модель:</b> ${m.model}<br><b>Признаки:</b> [${m.features}]</div>`;
            const cls = m.status === 'pending' ? 'bot pending' : 'bot';
            const icon = { completed: '✅', failed: '❌', pending: '⏳' }[m.status] || '❓';
            let text = `${icon} <b>${m.status}</b>`;
            if (m.output) text += `<br>Результат: <code>${JSON.stringify(m.output)}</code>`;
            if (m.uuid) text += `<br><small class="text-muted">${m.uuid}</small>`;
            return `<div class="chat-msg ${cls}">${text}</div>`;
        }).join('');
    box.scrollTop = box.scrollHeight;
}

function startPolling(uuid, idx) {
    if (polls[uuid]) return;
    polls[uuid] = setInterval(async () => {
        const res = await api('GET', `/predict/${uuid}`);
        if (res.ok && res.data.status !== 'pending') {
            clearInterval(polls[uuid]);
            delete polls[uuid];
            messages[idx].status = res.data.status;
            messages[idx].output = res.data.output_data;
            saveMessages();
            renderMessages();
        }
    }, 2000);
}

export const ChatPage = {
    render: () => `
        <div class="d-flex flex-column" style="height:calc(100vh - 2rem)">
            <h4 class="mb-3"><i class="bi bi-chat-dots me-2"></i>ML Чат</h4>
            <div class="chat-box flex-grow-1 border rounded bg-white p-3 mb-3" id="chat-box"></div>
            <form id="f-chat" class="d-flex gap-2">
                <select class="form-select" id="c-model" style="width:180px" required>
                    <option value="">Модель...</option>
                </select>
                <input type="text" class="form-control" id="c-features" placeholder="Признаки через запятую: 1, -2, 3" required>
                <button class="btn btn-primary text-nowrap" type="submit"><i class="bi bi-send"></i> Отправить</button>
            </form>
            <div class="mt-2"><button class="btn btn-sm btn-outline-secondary" id="btn-clear-chat">Очистить чат</button></div>
        </div>`,
    async init() {
        const sel = document.getElementById('c-model');
        const res = await api('GET', '/models/');
        if (res.ok) {
            res.data.forEach(m => {
                sel.insertAdjacentHTML('beforeend', `<option value="${m.id}" data-name="${m.name}">${m.name} (${m.cost_per_prediction}₽)</option>`);
            });
        }

        renderMessages();
        messages.forEach((m, i) => { if (m.role === 'bot' && m.status === 'pending' && m.uuid) startPolling(m.uuid, i); });

        document.getElementById('f-chat').onsubmit = async (e) => {
            e.preventDefault();
            const modelId = parseInt(sel.value);
            const modelName = sel.selectedOptions[0]?.dataset.name || '?';
            const raw = document.getElementById('c-features').value;
            const features = raw.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
            if (!modelId || features.length === 0) { toast('Выберите модель и введите признаки', 'warning'); return; }

            messages.push({ role: 'user', model: modelName, features });
            saveMessages(); renderMessages();

            const r = await api('POST', '/predict/', { model_id: modelId, features });
            if (r.ok) {
                const botIdx = messages.length;
                messages.push({ role: 'bot', status: r.data.status, uuid: r.data.task_id, output: r.data.output_data || null });
                saveMessages(); renderMessages();
                if (r.data.status === 'pending') startPolling(r.data.task_id, botIdx);
            } else {
                messages.push({ role: 'bot', status: 'failed', output: { error: r.data.detail } });
                saveMessages(); renderMessages();
            }
            document.getElementById('c-features').value = '';
        };

        document.getElementById('btn-clear-chat').onclick = () => {
            Object.values(polls).forEach(clearInterval);
            messages = []; saveMessages(); renderMessages();
        };
    }
};
