import { api, toast } from '../api.js';

export const WalletPage = {
    render: () => `
        <h4 class="mb-4"><i class="bi bi-wallet2 me-2"></i>Кошелёк</h4>
        <div class="row g-4">
            <div class="col-md-6">
                <div class="card shadow-sm border-0">
                    <div class="card-body text-center py-5">
                        <div class="text-muted mb-1">Текущий баланс</div>
                        <h1 class="display-4 fw-bold" id="w-balance">—</h1>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card shadow-sm border-0">
                    <div class="card-body">
                        <h5 class="card-title">Пополнить</h5>
                        <form id="f-deposit">
                            <div class="input-group mb-3">
                                <input type="number" class="form-control" id="w-amount" min="1" step="any" placeholder="Сумма" required>
                                <button class="btn btn-success" type="submit">Пополнить</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>`,
    async init() {
        const res = await api('GET', '/balance/');
        if (res.ok) document.getElementById('w-balance').textContent = res.data.balance.toFixed(2) + ' ₽';

        document.getElementById('f-deposit').onsubmit = async (e) => {
            e.preventDefault();
            const amount = parseFloat(document.getElementById('w-amount').value);
            const r = await api('POST', '/balance/deposit', { amount });
            if (r.ok) {
                document.getElementById('w-balance').textContent = r.data.balance.toFixed(2) + ' ₽';
                document.getElementById('w-amount').value = '';
                toast(`Пополнено на ${amount} ₽`);
            } else toast(r.data.detail || 'Ошибка', 'danger');
        };
    }
};
