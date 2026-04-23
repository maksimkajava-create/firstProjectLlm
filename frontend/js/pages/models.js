import { api } from '../api.js';

export const ModelsPage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-boxes me-2"></i>Доступные модели</h4>
        <div class="row g-3" id="models-list"><div class="text-center py-5 text-muted">Загрузка...</div></div>`,
    async init() {
        const res = await api('GET', '/models/');
        const box = document.getElementById('models-list');
        if (!res.ok || res.data.length === 0) { box.innerHTML = '<div class="text-muted">Моделей нет</div>'; return; }
        box.innerHTML = res.data.map(m => `
            <div class="col-md-4">
                <div class="card shadow-sm border-0 h-100">
                    <div class="card-body">
                        <h5><i class="bi bi-diagram-3 me-1"></i>${m.name}</h5>
                        <p class="text-muted">${m.description || 'Без описания'}</p>
                        <span class="badge bg-primary fs-6">${m.cost_per_prediction} ₽ / запрос</span>
                    </div>
                    <div class="card-footer bg-transparent border-0">
                        <a href="#chat" class="btn btn-outline-primary btn-sm w-100">Использовать</a>
                    </div>
                </div>
            </div>`).join('');
    }
};
