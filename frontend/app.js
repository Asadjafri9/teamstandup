const API = '';

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'HTTP ' + res.status);
  }
  return res;
}

async function apiJSON(path, options = {}) {
  const res = await api(path, options);
  return res.json();
}

function toast(msg, isError = false) {
  const t = document.createElement('div');
  t.className = 'toast' + (isError ? ' toast-error' : '');
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.remove(); }, 3000);
}

function redirect(path) {
  window.location.href = path;
}

function getUser() {
  return apiJSON('/api/me').catch(function() { return null; });
}

function renderApp(strings, ...values) {
  let html = strings[0];
  for (var i = 0; i < values.length; i++) {
    html += values[i];
    html += strings[i + 1];
  }
  const app = document.getElementById('app');
  app.innerHTML = html;
  app.classList.remove('loading');
}

function requireAuth(callback) {
  getUser().then(function(user) {
    if (!user) {
      redirect('/');
      return;
    }
    callback(user);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  var div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderMarkdown(md) {
  if (!md) return '';
  var html = escapeHtml(md);
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, function(m) { return '<ul>' + m + '</ul>'; });
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';
  html = html.replace(/<p><\/p>/g, '');
  return html;
}

function colorCodeBrief(html) {
  html = html.replace(/\b(blocked|blocker|stuck|blocking)\b/gi, '<span class="cc-blocker">$1</span>');
  html = html.replace(/\b(shipped|completed|done|progress|finished)\b/gi, '<span class="cc-progress">$1</span>');
  html = html.replace(/\b(new joiner|new member|welcome|first standup)\b/gi, '<span class="cc-new">$1</span>');
  html = html.replace(/\b(missing|hasn.t submitted|no submission|absent)\b/gi, '<span class="cc-missing">$1</span>');
  return html;
}
