const API='';
async function api(p,o={}){const r=await fetch(API+p,{...o,credentials:'include',headers:{'Content-Type':'application/json',...(o.headers||{})}});if(!r.ok){const e=await r.json().catch(()=>({detail:'Request failed'}));throw new Error(e.detail||`HTTP ${r.status}`)}return r}
async function apiJSON(p,o={}){return (await api(p,o)).json()}
function toast(m,e=false){const t=document.createElement('div');t.className='toast'+(e?' toast-error':'');t.textCo.loading{display:flex;align-items:center;justify-content:center;min-height:100vh}di.toast{position:fixed;bottom:1.5rem;right:1.5rem;padding:1rem 1.5rem;background:var(--ink);color:var(--ghost);border-radius:.25rem;z-index:1000;animation:reveal-up .3s ease}.toast-error{background:var(--destructive)}stCSSEOF

cat > frontend/app.js << 'JSEOF'
const API='';
async function api(p,o={}){const r=await fetch(API+p,{...o,credentials:'include',headers:{'Content-Type':'application/json',...(o.headers||{})}});if(!r.ok){cons);asynceplace(/^# (.+)$/gm,'<h1>$1</h1>');h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');h=h.replace(/`(.+?)`/g,'<code>$1</code>');h=h.replace(/^- (.+)$/gm,'<li>$1</li>');h=h.replace(/(<li>.*<\/li>\n?)+/g,m=>'<ul>'+m+'</ul>');h=h.replace(/\n\n/g,'</p><p>');h='<p>'+h+'</p>';h=h.replace(/<p><\/p>/g,'');return h}
function colorCodeBrief(h){h=h.replace(/\b(blocked|blocker|stuck|blocking)\b/gi,'<span class="cc-blocker">$1</span>');h=h.replace(/\b(shipped|completed|done|progress|finished)\b/gi,'<span class="cc-progress">$1</span>');h=h.replace(/\b(new joiner|new member|welcome|first standup)\b/gi,'<span class="cc-new">$1</span>');h=h.replace(/\b(missing|hasn't submitted|no submission|absent)\b/gi,'<span class="cc-missing">$1</span>');return h}
