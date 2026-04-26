import { api, toast } from '../api.js';

let messages = JSON.parse(localStorage.getItem('chatMessages') || '[]');
let polls = {};
let modelsCache = [];

function saveMessages() { localStorage.setItem('chatMessages', JSON.stringify(messages)); }

function renderMessages() {
    const box = document.getElementById('chat-box');
    if (!box) return;
    if (messages.length === 0) {
        box.innerHTML = '<div class="text-muted text-center mt-5">Отправьте первый запрос ↓</div>';
        return;
    }
    box.innerHTML = messages.map(m => {
        if (m.role === 'user') {
            const text = m.prompt || `[${m.features}]`;
            return `<div class="chat-msg user">${text}</div>`;
        }
        const cls = m.status === 'pending' ? 'bot pending' : 'bot';
        const icon = { completed: '✅', failed: '❌', pending: '⏳' }[m.status] || '❓';
        let text = '';
        if (m.output?.response) {
            text = m.output.response.replace(/\n/g, '<br>');
        } else if (m.output?.label) {
            text = `Класс: <b>${m.output.label}</b>`;
        } else if (m.output?.error) {
            text = `<span class="text-danger">${m.output.error}</span>`;
        } else {
            text = `${m.status}...`;
        }
        return `<div class="chat-msg ${cls}">${icon} ${text}</div>`;
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

function getSelectedModel() {
    const sel = document.getElementById('c-model');
    const opt = sel.selectedOptions[0];
    if (!opt || !opt.value) return null;
    return modelsCache.find(m => m.id === parseInt(opt.value));
}

export const ChatPage = {
    render: () => `
        <div class="d-flex flex-column" style="height:calc(100vh - 2rem)">
            <h4 class="mb-3"><i class="bi bi-chat-dots me-2"></i>ML Чат</h4>
            <div class="chat-box flex-grow-1 border rounded bg-white p-3 mb-3" id="chat-box"></div>
            <form id="f-chat" class="d-flex gap-2">
                <select class="form-select" id="c-model" style="width:200px" required>
                    <option value="">Модель...</option>
                </select>
                <input type="text" class="form-control" id="c-input" required>
                <button class="btn btn-primary text-nowrap" type="submit"><i class="bi bi-send"></i></button>
            </form>
            <small class="text-muted mt-1" id="model-hint">Выберите модель</small>
            <button class="btn btn-sm btn-outline-secondary mt-2" style="width:fit-content" id="btn-clear-chat">Очистить чат</button>
        </div>`,
    async init() {
        const sel = document.getElementById('c-model');
        const hint = document.getElementById('model-hint');
        const input = document.getElementById('c-input');
        const res = await api('GET', '/models/');

        if (res.ok) {
            modelsCache = res.data;
            res.data.forEach(m => {
                const icon = m.model_type === 'llm' ? '🤖' : '📊';
                sel.insertAdjacentHTML('beforeend',
                    `<option value="${m.id}">${icon} ${m.name} (${m.cost_per_prediction}₽)</option>`
                );
            });
        }

        sel.onchange = () => {
            const m = getSelectedModel();
            if (!m) return;
            if (m.model_type === 'llm') {
                hint.textContent = '🤖 Режим LLM — пишите текст';
                input.placeholder = 'Напишите сообщение...';
            } else {
                hint.textContent = '📊 Классификатор — числа через запятую';
                input.placeholder = 'Например: 1, -2, 3';
            }
        };

        renderMessages();
        messages.forEach((m, i) => {
            if (m.role === 'bot' && m.status === 'pending' && m.uuid) startPolling(m.uuid, i);
        });

        document.getElementById('f-chat').onsubmit = async (e) => {
            e.preventDefault();
            const model = getSelectedModel();
            if (!model) { toast('Выберите модель', 'warning'); return; }

            const raw = input.value.trim();
            if (!raw) return;

            let body = { model_id: model.id };
            let userMsg = { role: 'user' };

            if (model.model_type === 'llm') {
                body.prompt = raw;
                userMsg.prompt = raw;
            } else {
                const nums = raw.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                if (nums.length === 0) { toast('Введите числа через запятую', 'warning'); return; }
                body.features = nums;
                userMsg.features = nums;
            }

            messages.push(userMsg);
            saveMessages();
            renderMessages();

            const r = await api('POST', '/predict/', body);
            if (r.ok) {
                const botIdx = messages.length;
                messages.push({ role: 'bot', status: r.data.status, uuid: r.data.task_id, output: null });
                saveMessages();
                renderMessages();
                if (r.data.status === 'pending') startPolling(r.data.task_id, botIdx);
            } else {
                messages.push({ role: 'bot', status: 'failed', output: { error: r.data.detail } });
                saveMessages();
                renderMessages();
            }
            input.value = '';
        };

        document.getElementById('btn-clear-chat').onclick = () => {
            Object.values(polls).forEach(clearInterval);
            messages = [];
            saveMessages();
            renderMessages();
        };
    }
};
