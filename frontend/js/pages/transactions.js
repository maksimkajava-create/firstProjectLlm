import { api } from '../api.js';

export const TransactionsPage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-receipt me-2"></i>История транзакций</h4>
        <div class="card shadow-sm border-0"><div class="card-body p-0">
            <div class="table-responsive"><table class="table table-hover mb-0">
                <thead class="table-light"><tr><th>#</th><th>Дата</th><th>Тип</th><th>Сумма</th><th>Задача</th></tr></thead>
                <tbody id="t-body"><tr><td colspan="5" class="text-center py-3">Загрузка...</td></tr></tbody>
            </table></div>
        </div></div>`,
    async init() {
        const res = await api('GET', '/history/transactions');
        const tb = document.getElementById('t-body');
        if (!res.ok || res.data.length === 0) { tb.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Пусто</td></tr>'; return; }
        tb.innerHTML = res.data.map((t, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>${new Date(t.created_at).toLocaleString()}</td>
                <td><span class="badge ${t.transaction_type === 'credit' ? 'bg-success' : 'bg-danger'}">${t.transaction_type}</span></td>
                <td>${t.amount.toFixed(2)} ₽</td>
                <td>${t.task_id ?? '—'}</td>
            </tr>`).join('');
    }
};
