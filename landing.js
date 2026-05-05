document.addEventListener('DOMContentLoaded', () => {

    // ── Auth State ──────────────────────────────────────────────────────
    let authToken = localStorage.getItem('bg_token') || null;
    let authUser  = JSON.parse(localStorage.getItem('bg_user') || 'null');

    function updateNavAuth() {
        const navAuth = document.getElementById('nav-auth');
        const navUser = document.getElementById('nav-user');
        const navName = document.getElementById('nav-username');
        if (authToken && authUser) {
            navAuth.classList.add('hidden');
            navUser.classList.remove('hidden');
            navName.textContent = `👤 ${authUser.username} (${authUser.phc || authUser.role})`;
        } else {
            navAuth.classList.remove('hidden');
            navUser.classList.add('hidden');
        }
    }
    updateNavAuth();

    window.logout = () => {
        localStorage.removeItem('bg_token');
        localStorage.removeItem('bg_user');
        authToken = null; authUser = null;
        updateNavAuth();
    };

    // ── Modal Helpers ───────────────────────────────────────────────────
    window.openModal   = id => document.getElementById(id).classList.remove('hidden');
    window.closeModal  = id => document.getElementById(id).classList.add('hidden');
    window.switchModal = (a, b) => { closeModal(a); openModal(b); };

    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) overlay.classList.add('hidden');
        });
    });

    // ── Register ────────────────────────────────────────────────────────
    window.doRegister = async () => {
        const username = document.getElementById('reg-username').value.trim();
        const password = document.getElementById('reg-password').value;
        const phc      = document.getElementById('reg-phc').value.trim();
        const role     = document.getElementById('reg-role').value;
        const errEl    = document.getElementById('reg-error');

        errEl.classList.add('hidden');
        if (!username || !password) { showError(errEl, 'Username and password required'); return; }
        if (password.length < 6)    { showError(errEl, 'Password must be at least 6 characters'); return; }

        try {
            const res  = await api('/api/auth/register', 'POST', { username, password, phc, role });
            const data = await res.json();
            if (!res.ok) { showError(errEl, data.error); return; }
            closeModal('register-modal');
            openModal('login-modal');
            document.getElementById('login-username').value = username;
        } catch { showError(errEl, 'Connection error'); }
    };

    // ── Login ───────────────────────────────────────────────────────────
    window.doLogin = async () => {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errEl    = document.getElementById('login-error');

        errEl.classList.add('hidden');
        if (!username || !password) { showError(errEl, 'Enter username and password'); return; }

        try {
            const res  = await api('/api/auth/login', 'POST', { username, password });
            const data = await res.json();
            if (!res.ok) { showError(errEl, data.error); return; }

            authToken = data.token;
            authUser  = { username: data.username, role: data.role, phc: data.phc };
            localStorage.setItem('bg_token', authToken);
            localStorage.setItem('bg_user', JSON.stringify(authUser));
            closeModal('login-modal');
            updateNavAuth();
        } catch { showError(errEl, 'Connection error'); }
    };

    function showError(el, msg) {
        el.textContent = msg;
        el.classList.remove('hidden');
    }

    // ── API Helper ──────────────────────────────────────────────────────
    function api(url, method = 'GET', body = null) {
        const headers = { 'Content-Type': 'application/json' };
        if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
        return fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : undefined
        });
    }

    // ── Stats Bar ───────────────────────────────────────────────────────
    async function fetchStats() {
        try {
            const res  = await api('/api/stats');
            const data = await res.json();
            document.getElementById('stat-total').textContent  = data.total;
            document.getElementById('stat-high').textContent   = data.high;
            document.getElementById('stat-medium').textContent = data.medium;
            document.getElementById('stat-low').textContent    = data.low;
        } catch { /* silent */ }
    }

    // ── Alerts Feed ─────────────────────────────────────────────────────
    async function fetchAlerts() {
        const feed = document.getElementById('alerts-feed');
        if (!feed) return;
        try {
            const res  = await api('/api/alerts');
            const data = await res.json();

            if (!data.length) {
                feed.innerHTML = '<div class="loading-msg">No active alerts.</div>';
                return;
            }

            feed.innerHTML = data.map(a => `
                <div class="alert-item ${a.risk_level}">
                    <div class="alert-item-header">
                        <span class="alert-item-name ${a.risk_level}">${a.risk_level} Risk — ${a.patient_name}</span>
                        <span class="alert-item-time">${a.time}</span>
                    </div>
                    <div class="alert-item-meta">${a.explanation} | ${a.phc}</div>
                </div>
            `).join('');
        } catch (err) {
            feed.innerHTML = '<div class="loading-msg" style="color:#ef4444;">Could not load alerts. Is the server running?</div>';
        }
    }

    // ── Vitals Submission ───────────────────────────────────────────────
    const saveBtn = document.getElementById('save-vitals-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const systolic  = document.getElementById('vitals-systolic').value;
            const diastolic = document.getElementById('vitals-diastolic').value;
            const spo2      = document.getElementById('vitals-spo2').value;
            const fhr       = document.getElementById('vitals-fhr').value;
            const age       = document.getElementById('vitals-age').value;
            const week      = document.getElementById('vitals-week').value;
            const name      = document.getElementById('vitals-name').value.trim() || `Patient-${Date.now()}`;
            const phc       = document.getElementById('vitals-phc').value.trim() || (authUser?.phc || 'Field Entry');

            if (!systolic || !diastolic || !spo2 || !fhr) {
                alert('Please fill in all vital signs (BP, SpO2, FHR)');
                return;
            }

            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analysing...';
            saveBtn.disabled  = true;

            try {
                const res  = await api('/api/save_vitals', 'POST', {
                    systolic: +systolic, diastolic: +diastolic,
                    spo2: +spo2, fhr: +fhr,
                    age: +age, gestational_week: +week,
                    patient_name: name, phc,
                    recorded_by: authUser?.username || 'anonymous'
                });
                const result = await res.json();

                if (!res.ok) { alert('Error: ' + result.error); return; }

                showResult(result);
                fetchAlerts();
                fetchStats();
            } catch (err) {
                alert('Connection error — is the Flask server running?\n\n' + err.message);
            } finally {
                saveBtn.innerHTML = '<i class="fas fa-brain"></i> Analyse with ML Model';
                saveBtn.disabled  = false;
            }
        });
    }

    function showResult(result) {
        const panel = document.getElementById('result-panel');
        panel.classList.remove('hidden');

        // Risk badge
        const badge = document.getElementById('result-risk-badge');
        const icons = { Low: '✅', Medium: '⚠️', High: '🚨' };
        badge.textContent  = `${icons[result.risk_level]} ${result.risk_level} Risk`;
        badge.className    = `risk-badge ${result.risk_level}`;

        // Confidence bar
        const pct = (result.confidence * 100).toFixed(1);
        document.getElementById('confidence-bar').style.width = pct + '%';
        document.getElementById('confidence-pct').textContent = pct + '%';

        // Probabilities
        document.getElementById('prob-low').textContent    = (result.probabilities.low    * 100).toFixed(1) + '%';
        document.getElementById('prob-medium').textContent = (result.probabilities.medium * 100).toFixed(1) + '%';
        document.getElementById('prob-high').textContent   = (result.probabilities.high   * 100).toFixed(1) + '%';

        // Recommendations
        document.getElementById('recommendations-list').innerHTML =
            result.recommendations.map(r => `<div class="rec-item">${r}</div>`).join('');

        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // ── CTG Waveform ────────────────────────────────────────────────────
    const canvas = document.getElementById('ctgWaveform');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let x = 0, points = [];

        const draw = () => {
            const rect = canvas.parentNode.getBoundingClientRect();
            canvas.width  = rect.width;
            canvas.height = rect.height;

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.strokeStyle = '#00a6a6';
            ctx.lineWidth   = 2;
            ctx.beginPath();

            const base = canvas.height / 2;
            const y    = base + Math.sin(x * 0.05) * 18 + Math.sin(x * 0.13) * 7 + (Math.random() - 0.5) * 3;
            points.push({ x: canvas.width, y });
            if (points.length > 220) points.shift();

            points.forEach((p, i) => {
                p.x -= 2;
                i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
            });
            ctx.stroke();
            x++;
            requestAnimationFrame(draw);
        };
        draw();
    }

    // ── Heatmap Tooltips ────────────────────────────────────────────────
    document.querySelectorAll('.heatmap-marker').forEach(marker => {
        marker.addEventListener('mouseenter', () => {
            const tip = document.createElement('div');
            tip.className = 'heatmap-tooltip';
            tip.innerHTML = `<strong>${marker.dataset.phc || 'PHC'}</strong><br>
                Status: ${marker.classList.contains('high-risk') ? '🔴 High Risk' : '🟡 Monitoring'}`;
            Object.assign(tip.style, {
                position:'absolute', background:'rgba(15,23,42,0.95)',
                color:'white', padding:'8px 12px', borderRadius:'8px',
                fontSize:'0.75rem', top:'-55px', left:'50%',
                transform:'translateX(-50%)', pointerEvents:'none',
                whiteSpace:'nowrap', zIndex:'100', lineHeight:'1.5'
            });
            marker.appendChild(tip);
        });
        marker.addEventListener('mouseleave', () => {
            marker.querySelector('.heatmap-tooltip')?.remove();
        });
    });

    // ── Scroll Reveal ───────────────────────────────────────────────────
    const reveals = document.querySelectorAll('.reveal');
    const revealOnScroll = () => {
        reveals.forEach(el => {
            if (el.getBoundingClientRect().top < window.innerHeight - 120)
                el.classList.add('active');
        });
    };
    window.addEventListener('scroll', revealOnScroll);
    revealOnScroll();

    // ── Smooth Scroll ───────────────────────────────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
            e.preventDefault();
            document.querySelector(a.getAttribute('href'))
                ?.scrollIntoView({ behavior: 'smooth' });
        });
    });

    // ── Init ────────────────────────────────────────────────────────────
    fetchAlerts();
    fetchStats();
    setInterval(() => { fetchAlerts(); fetchStats(); }, 10000);
});
