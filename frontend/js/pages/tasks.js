import { api, toast } from '../api.js';

export const TasksPage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-list-task me-2"></i>История задач</h4>
        <div class="card shadow-sm border-0"><div class="card-body p-0">
            <div class="table-responsive"><table class="table table-hover mb-0">
                <thead class="table-light"><tr><th>#</th><th>UUID</th><th>Модель</th><th>Вход</th><th>Выход</th><th>Статус</th><th>Дата</th></tr></thead>
                <tbody id="tasks-body"><tr><td colspan="7" class="text-center py-3">Загрузка...</td></tr></tbody>
            </table></div>
        </div></div>`,
    async init() {
        const res = await api('GET', '/history/tasks');
        const tb = document.getElementById('tasks-body');
        if (!res.ok || res.data.length === 0) { tb.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">Пусто</td></tr>'; return; }
        const badge = s => ({ completed: 'bg-success', failed: 'bg-danger', pending: 'bg-warning text-dark' }[s] || 'bg-secondary');
        tb.innerHTML = res.data.map((t, i) => `
            <tr>
                <td>${i + 1}</td>
                <td><code class="copy-uuid" role="button" title="Копировать">${(t.task_uuid || '—').slice(0, 8)}…</code></td>
                <td>${t.model_id}</td>
                <td><small>${JSON.stringify(t.input_data)}</small></td>
                <td><small>${t.output_data ? JSON.stringify(t.output_data) : '—'}</small></td>
                <td><span class="badge ${badge(t.status)}">${t.status}</span></td>
                <td><small>${new Date(t.created_at).toLocaleString()}</small></td>
            </tr>`).join('');
        tb.querySelectorAll('.copy-uuid').forEach(el => {
            el.onclick = () => { navigator.clipboard.writeText(el.textContent.replace('…', '')); toast('UUID скопирован', 'info'); };
        });
    }
};
