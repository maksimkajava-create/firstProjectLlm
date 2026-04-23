import { getToken, clearToken, api, setCurrentUser, currentUser } from './api.js';
import { LoginPage, RegisterPage, ResetPage } from './pages/auth.js';
import { ChatPage } from './pages/chat.js';
import { WalletPage } from './pages/wallet.js';
import { TransactionsPage } from './pages/transactions.js';
import { TasksPage } from './pages/tasks.js';
import { ProfilePage } from './pages/profile.js';
import { ModelsPage } from './pages/models.js';
import { AdminPage } from './pages/admin.js';

const authPages = { login: LoginPage, register: RegisterPage, reset: ResetPage };
const appPages = { chat: ChatPage, wallet: WalletPage, transactions: TransactionsPage, tasks: TasksPage, profile: ProfilePage, models: ModelsPage, admin: AdminPage };

function showLayout(name) {
    document.getElementById('auth-layout').classList.toggle('d-none', name !== 'auth');
    document.getElementById('app-layout').classList.toggle('d-none', name !== 'app');
}

function highlightNav(hash) {
    document.querySelectorAll('#nav-links .nav-link').forEach(a => {
        a.classList.toggle('active-link', a.getAttribute('href') === '#' + hash);
    });
}

async function loadUser() {
    if (!getToken()) return false;
    const res = await api('GET', '/users/me');
    if (!res.ok) return false;
    setCurrentUser(res.data);
    document.getElementById('sidebar-user').textContent = res.data.email;
    const adminNav = document.getElementById('nav-admin');
    if (res.data.role === 'admin') adminNav.classList.remove('d-none');
    else adminNav.classList.add('d-none');
    return true;
}

async function route() {
    const hash = (location.hash || '#login').slice(1);

    if (authPages[hash]) {
        showLayout('auth');
        const page = authPages[hash];
        document.getElementById('auth-content').innerHTML = page.render();
        page.init();
        return;
    }

    const loggedIn = await loadUser();
    if (!loggedIn) { location.hash = '#login'; return; }

    const page = appPages[hash];
    if (!page) { location.hash = '#chat'; return; }

    showLayout('app');
    highlightNav(hash);
    document.getElementById('main-content').innerHTML = '<div class="text-center p-5"><div class="spinner-border"></div></div>';
    document.getElementById('main-content').innerHTML = page.render();
    await page.init();
}

document.getElementById('btn-logout')?.addEventListener('click', () => {
    clearToken();
    location.hash = '#login';
});

window.addEventListener('hashchange', route);
route();
