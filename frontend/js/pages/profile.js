import { api, toast, currentUser } from '../api.js';

export const ProfilePage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-person me-2"></i>Профиль</h4>
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card shadow-sm border-0">
                    <div class="card-body">
                        <h5 class="card-title">Информация</h5>
                        <table class="table mb-0">
                            <tr><th>ID</th><td id="p-id">—</td></tr>
                            <tr><th>Email</th><td id="p-email">—</td></tr>
                            <tr><th>Роль</th><td id="p-role">—</td></tr>
                            <tr><th>Баланс</th><td id="p-balance">—</td></tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm border-0 mb-3">
                    <div class="card-body">
                        <h5 class="card-title">Изменить email</h5>
                        <form id="f-email">
                            <div class="mb-2"><input type="email" class="form-control" id="p-new-email" placeholder="Новый email" required></div>
                            <button class="btn btn-outline-primary btn-sm" type="submit">Сохранить</button>
                        </form>
                    </div>
                </div>
                <div class="card shadow-sm border-0">
                    <div class="card-body">
                        <h5 class="card-title">Сменить пароль</h5>
                        <form id="f-pwd">
                            <div class="mb-2"><input type="password" class="form-control" id="p-old-pwd" placeholder="Текущий пароль" required></div>
                            <div class="mb-2"><input type="password" class="form-control" id="p-new-pwd" placeholder="Новый пароль" minlength="8" required></div>
                            <button class="btn btn-outline-primary btn-sm" type="submit">Сменить</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>`,
    async init() {
        const res = await api('GET', '/users/me');
        if (!res.ok) return;
        const u = res.data;
        document.getElementById('p-id').textContent = u.id;
        document.getElementById('p-email').textContent = u.email;
        document.getElementById('p-role').textContent = u.role;
        document.getElementById('p-balance').textContent = u.account ? u.account.balance.toFixed(2) + ' ₽' : '—';

        document.getElementById('f-email').onsubmit = async (e) => {
            e.preventDefault();
            const r = await api('PATCH', '/users/me', { email: document.getElementById('p-new-email').value });
            if (r.ok) { toast('Email обновлён'); location.hash = '#profile'; }
            else toast(r.data.detail || 'Ошибка', 'danger');
        };

        document.getElementById('f-pwd').onsubmit = async (e) => {
            e.preventDefault();
            const r = await api('PATCH', '/users/me', {
                old_password: document.getElementById('p-old-pwd').value,
                new_password: document.getElementById('p-new-pwd').value,
            });
            if (r.ok) { toast('Пароль изменён'); document.getElementById('f-pwd').reset(); }
            else toast(r.data.detail || 'Ошибка', 'danger');
        };
    }
};
