import { api, setToken, toast } from '../api.js';

export const LoginPage = {
    render: () => `
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h4 class="mb-3">Вход</h4>
                <form id="f-login">
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" id="l-email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Пароль</label>
                        <input type="password" class="form-control" id="l-pass" required>
                    </div>
                    <button class="btn btn-primary w-100" type="submit">Войти</button>
                </form>
                <div class="text-center mt-3">
                    <a href="#register">Регистрация</a> · <a href="#reset">Забыли пароль?</a>
                </div>
            </div>
        </div>`,
    init() {
        document.getElementById('f-login').onsubmit = async (e) => {
            e.preventDefault();
            const res = await api('POST', '/auth/login', {
                username: document.getElementById('l-email').value,
                password: document.getElementById('l-pass').value,
            }, true);
            if (res.ok) {
                setToken(res.data.access_token);
                toast('Добро пожаловать!');
                location.hash = '#chat';
            } else {
                toast(res.data.detail || 'Ошибка входа', 'danger');
            }
        };
    }
};

export const RegisterPage = {
    render: () => `
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h4 class="mb-3">Регистрация</h4>
                <form id="f-reg">
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" id="r-email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Пароль (мин. 8 символов)</label>
                        <input type="password" class="form-control" id="r-pass" minlength="8" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Повторите пароль</label>
                        <input type="password" class="form-control" id="r-pass2" minlength="8" required>
                    </div>
                    <button class="btn btn-success w-100" type="submit">Зарегистрироваться</button>
                </form>
                <div class="text-center mt-3"><a href="#login">Уже есть аккаунт? Войти</a></div>
            </div>
        </div>`,
    init() {
        document.getElementById('f-reg').onsubmit = async (e) => {
            e.preventDefault();
            const pass = document.getElementById('r-pass').value;
            if (pass !== document.getElementById('r-pass2').value) {
                toast('Пароли не совпадают', 'danger'); return;
            }
            const res = await api('POST', '/auth/register', {
                email: document.getElementById('r-email').value,
                password: pass,
            });
            if (res.ok) {
                toast('Регистрация успешна! Войдите.');
                location.hash = '#login';
            } else {
                toast(res.data.detail || 'Ошибка', 'danger');
            }
        };
    }
};

export const ResetPage = {
    render: () => `
        <div class="card shadow-sm">
            <div class="card-body p-4">
                <h4 class="mb-3">Сброс пароля</h4>
                <form id="f-reset">
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" class="form-control" id="rs-email" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Новый пароль</label>
                        <input type="password" class="form-control" id="rs-pass" minlength="8" required>
                    </div>
                    <button class="btn btn-warning w-100" type="submit">Сбросить пароль</button>
                </form>
                <div class="text-center mt-3"><a href="#login">Назад ко входу</a></div>
            </div>
        </div>`,
    init() {
        document.getElementById('f-reset').onsubmit = async (e) => {
            e.preventDefault();
            const res = await api('POST', '/auth/reset-password', {
                email: document.getElementById('rs-email').value,
                new_password: document.getElementById('rs-pass').value,
            });
            if (res.ok) { toast('Пароль изменён!'); location.hash = '#login'; }
            else toast(res.data.detail || 'Ошибка', 'danger');
        };
    }
};
