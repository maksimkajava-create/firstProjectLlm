const BASE = '/api';

export let currentUser = null;

export function getToken() {
    return localStorage.getItem('token');
}

export function setToken(t) {
    localStorage.setItem('token', t);
}

export function clearToken() {
    localStorage.removeItem('token');
    currentUser = null;
}

export function setCurrentUser(u) {
    currentUser = u;
}

export async function api(method, path, body = null, isForm = false) {
    const headers = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const opts = { method, headers };

    if (body && isForm) {
        const fd = new URLSearchParams(body);
        opts.body = fd;
        headers['Content-Type'] = 'application/x-www-form-urlencoded';
    } else if (body) {
        opts.body = JSON.stringify(body);
        headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${BASE}${path}`, opts);

    if (res.status === 204) return { ok: true, status: 204, data: null };

    let data;
    try { data = await res.json(); } catch { data = {}; }

    if (res.status === 401) {
        clearToken();
        location.hash = '#login';
        return { ok: false, status: 401, data };
    }

    return { ok: res.ok, status: res.status, data };
}

export function toast(message, type = 'success') {
    const box = document.getElementById('toast-box');
    const colors = { success: 'bg-success', danger: 'bg-danger', warning: 'bg-warning text-dark', info: 'bg-info text-dark' };
    const id = 't' + Date.now();
    box.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast align-items-center text-white ${colors[type] || 'bg-secondary'} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    const el = document.getElementById(id);
    const t = new bootstrap.Toast(el, { delay: 3500 });
    t.show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
}
