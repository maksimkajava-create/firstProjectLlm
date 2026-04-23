import { api, toast } from '../api.js';

export const AdminPage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-shield-lock me-2"></i>Администрирование</h4>
        <ul class="nav nav-tabs mb-3" role="tablist">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-users">Пользователи</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-atasks">Задачи</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-models">Модели</button></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane fade show active" id="tab-users">
                <div class="table-responsive"><table class="table table-sm table-hover">
                    <thead><tr><th>ID</th><th>Email</th><th>Роль</th><th>Баланс</th></tr></thead>
                    <tbody id="a-users"></tbody>
                </table></div>
            </div>
            <div class="tab-pane fade" id="tab-atasks">
                <div class="table-responsive"><table class="table table-sm table-hover">
                    <thead><tr><th>ID</th><th>UUID</th><th>User</th><th>Model</th><th>Статус</th><th>Дата</th></tr></thead>
                    <tbody id="a-tasks"></tbody>
                </table></div>
            </div>
            <div class="tab-pane fade" id="tab-models">
                <form id="f-add-model" class="row g-2 mb-3">
                    <div class="col-auto"><input class="form-control form-control-sm" id="am-name" placeholder="Имя" required></div>
                    <div class="col-auto"><input class="form-control form-control-sm" id="am-desc" placeholder="Описание"></div>
                    <div class="col-auto"><input type="number" class="form-control form-control-sm" id="am-cost" placeholder="Цена" step="any" min="0.01" required></div>
                    <div class="col-auto"><button class="btn btn-success btn-sm" type="submit"><i class="bi bi-plus"></i> Добавить</button></div>
                </form>
                <div class="table-responsive"><table class="table table-sm table-hover">
                    <thead><tr><th>ID</th><th>Имя</th><th>Описание</th><th>Цена</th><th></th></tr></thead>
                    <tbody id="a-models"></tbody>
                </table></div>
            </div>
        </div>`,
    async init() {
        const badge = s => ({ completed: 'bg-success', failed: 'bg-danger', pending: 'bg-warning text-dark' }[s] || 'bg-secondary');

        const [uRes, tRes, mRes] = await Promise.all([
            api('GET', '/admin/users'),
            api('GET', '/admin/tasks'),
            api('GET', '/admin/models'),
        ]);

        if (uRes.ok) {
            document.getElementById('a-users').innerHTML = uRes.data.map(u =>
                `<tr><td>${u.id}</td><td>${u.email}</td><td><span class="badge ${u.role === 'admin' ? 'bg-danger' : 'bg-secondary'}">${u.role}</span></td><td>${u.balance.toFixed(2)}</td></tr>`
            ).join('') || '<tr><td colspan="4" class="text-muted">Пусто</td></tr>';
        }

        if (tRes.ok) {
            document.getElementById('a-tasks').innerHTML = tRes.data.map(t =>
                `<tr><td>${t.id}</td><td><code>${(t.task_uuid || '—').slice(0, 8)}</code></td><td>${t.user_id}</td><td>${t.model_id}</td><td><span class="badge ${badge(t.status)}">${t.status}</span></td><td>${new Date(t.created_at).toLocaleString()}</td></tr>`
            ).join('') || '<tr><td colspan="6" class="text-muted">Пусто</td></tr>';
        }

        const renderModels = (data) => {
            document.getElementById('a-models').innerHTML = data.map(m =>
                `<tr><td>${m.id}</td><td>${m.name}</td><td>${m.description || '—'}</td><td>${m.cost_per_prediction}</td><td><button class="btn btn-outline-danger btn-sm del-model" data-id="${m.id}"><i class="bi bi-trash"></i></button></td></tr>`
            ).join('');
            document.querySelectorAll('.del-model').forEach(btn => {
                btn.onclick = async () => {
                    if (!confirm('Удалить модель?')) return;
                    const r = await api('DELETE', `/admin/models/${btn.dataset.id}`);
                    if (r.ok) { toast('Модель удалена'); const mr = await api('GET', '/admin/models'); if (mr.ok) renderModels(mr.data); }
                    else toast(r.data.detail || 'Ошибка', 'danger');
                };
            });
        };
        if (mRes.ok) renderModels(mRes.data);

        document.getElementById('f-add-model').onsubmit = async (e) => {
            e.preventDefault();
            const r = await api('POST', '/admin/models', {
                name: document.getElementById('am-name').value,
                description: document.getElementById('am-desc').value,
                cost_per_prediction: parseFloat(document.getElementById('am-cost').value),
            });
            if (r.ok) {
                toast('Модель создана');
                document.getElementById('f-add-model').reset();
                const mr = await api('GET', '/admin/models');
                if (mr.ok) renderModels(mr.data);
            } else toast(r.data.detail || 'Ошибка', 'danger');
        };
    }
};
