/* Review input for the cluster pages and prototypes.
 *
 * Loaded by every page in this folder. Adds, to each thing the owner is asked about, three
 * tick buttons (Approve / Change / Drop), an option-number box where there is a prototype to
 * pick from, and a note box. Answers are kept in this browser (localStorage, one key per page)
 * and can be copied out as one block of text: this page's, or every page's at once.
 *
 * Nothing is sent anywhere. The pages work without this file; they just lose the inputs.
 */
(function () {
  'use strict';
  var page = decodeURIComponent(location.pathname.split('/').pop() || 'page');
  // One set of answers per review folder, so two reviews opened in the same browser never mix.
  var PREFIX = 'review-input:' + decodeURIComponent(location.pathname.replace(/[^/]*$/, '')) + ':';
  var KEY = PREFIX + page;
  var isIndex = page === 'index.html';
  var CHOICES = [['approve', 'Approve'], ['change', 'Change'], ['drop', 'Drop']];

  function read(key) {
    try { return JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch (e) { return {}; }
  }
  function write(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private window: keep in memory */ }
  }
  var state = read(KEY);

  // An item that links to exactly one prototype shares that prototype's answer, so a pick made
  // on the prototype shows on the page that links to it, and the other way round.
  function rec(t) {
    if (t.bind) return read(PREFIX + t.bind).pick || {};
    return state[t.id] || {};
  }
  function put(t, patch) {
    if (t.bind) {
      var st = read(PREFIX + t.bind);
      var cur = st.pick || (st.pick = {});
      Object.keys(patch).forEach(function (k) { cur[k] = patch[k]; });
      try { localStorage.setItem(PREFIX + t.bind, JSON.stringify(st)); } catch (e) { /* no storage */ }
    } else {
      var own = state[t.id] || (state[t.id] = {});
      Object.keys(patch).forEach(function (k) { own[k] = patch[k]; });
      write(state);
    }
    refresh();
  }

  var css = document.createElement('style');
  css.textContent = [
    '.ri{margin:14px 0 0;padding:12px 0 0;border-top:1px dashed #c9d2ce;font:15px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif;color:#1b2421}',
    '.ri-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}',
    '.ri button.ri-c{font:inherit;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid #b9c4bf;background:#fff;color:#1b2421;cursor:pointer}',
    '.ri button.ri-c[aria-pressed="true"]{color:#fff}',
    '.ri button.ri-c[data-v="approve"][aria-pressed="true"]{background:#0b6b5c;border-color:#0b6b5c}',
    '.ri button.ri-c[data-v="change"][aria-pressed="true"]{background:#8a5a00;border-color:#8a5a00}',
    '.ri button.ri-c[data-v="drop"][aria-pressed="true"]{background:#b3261e;border-color:#b3261e}',
    '.ri label.ri-opt{display:inline-flex;align-items:center;gap:6px;font-weight:600}',
    '.ri input.ri-o{font:inherit;width:64px;padding:6px 8px;border:1px solid #b9c4bf;border-radius:8px;background:#fff;color:#1b2421}',
    '.ri textarea.ri-n{display:block;width:100%;min-height:38px;margin-top:8px;padding:8px 10px;font:inherit;border:1px solid #b9c4bf;border-radius:8px;background:#fff;color:#1b2421;resize:vertical;box-sizing:border-box}',
    '.ri-bar{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;background:#1b2421;color:#fff;font:14px/1.3 system-ui,-apple-system,"Segoe UI",sans-serif;padding:8px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center;box-shadow:0 -2px 10px rgba(0,0,0,.25)}',
    '.ri-bar b{font-weight:700}',
    '.ri-bar button{font:inherit;font-weight:600;padding:6px 12px;border-radius:8px;border:1px solid #fff;background:transparent;color:#fff;cursor:pointer}',
    '.ri-bar button.ri-main{background:#fff;color:#1b2421}',
    '.ri-bar .ri-msg{opacity:.85}',
    '.ri-bar a{color:#fff}',
    '.ri-out{position:fixed;left:16px;right:16px;bottom:56px;z-index:2147483000;display:none}',
    '.ri-out textarea{display:block;width:100%;height:42vh;padding:12px;font:13px/1.45 ui-monospace,Menlo,Consolas,monospace;border:2px solid #1b2421;border-radius:10px;background:#fff;color:#1b2421;box-sizing:border-box}',
    '.ri-float{position:fixed;right:16px;bottom:60px;z-index:2147482000;width:340px;max-width:calc(100vw - 32px);background:#fff;border:2px solid #1b2421;border-radius:12px;padding:12px 14px;box-shadow:0 6px 24px rgba(0,0,0,.25)}',
    '.ri-float .ri{margin:0;padding:0;border:0}',
    '.ri-float h4{margin:0 0 8px;font:700 15px/1.3 system-ui,-apple-system,"Segoe UI",sans-serif;color:#1b2421;display:flex;justify-content:space-between;align-items:center;gap:12px}',
    '.ri-float .ri-fold{font:600 13px/1 system-ui,-apple-system,"Segoe UI",sans-serif;padding:6px 10px;border-radius:8px;border:1px solid #b9c4bf;background:#fff;color:#1b2421;cursor:pointer;white-space:nowrap}',
    '.ri-float.ri-closed{width:auto;padding:8px 10px}',
    '.ri-float.ri-closed h4{margin:0}',
    '.ri-float.ri-closed .ri{display:none}',
    '.ri-count{font-size:12px;font-weight:700;color:#0b6b5c;margin-left:8px}',
    'body{padding-bottom:64px !important}'
  ].join('\n');
  document.head.appendChild(css);

  function text(el) { return (el ? el.textContent : '').replace(/\s+/g, ' ').trim(); }

  // What can be answered on this page.
  var targets = [];
  function add(id, label, host, wantsOption, floating, bind) {
    targets.push({ id: id, label: label, host: host, wantsOption: wantsOption, floating: floating, bind: bind || '' });
  }
  function protoOf(el) {
    var seen = {};
    el.querySelectorAll('a[href^="prototype-"]').forEach(function (a) { seen[a.getAttribute('href').split('#')[0]] = 1; });
    var files = Object.keys(seen);
    return files.length === 1 ? files[0] : '';
  }
  if (!isIndex) {
    document.querySelectorAll('section.group-head[id]').forEach(function (s) {
      add(s.id, text(s.querySelector('h2')), s, false);
    });
    document.querySelectorAll('section.item[id]').forEach(function (s) {
      var head = s.querySelector('h3, h2');
      add(s.id, text(head), s, !!s.querySelector('a[href^="prototype-"]'), false, protoOf(s));
    });
    if (!targets.length) {
      document.querySelectorAll('section').forEach(function (s) {
        var idEl = s.querySelector('h2 > .id');
        if (idEl) add(text(idEl), text(s.querySelector('h2')), s, false);
      });
    }
    if (!targets.length) {
      document.querySelectorAll('a.item[href]').forEach(function (a) {
        // a list of prototypes (cluster2-prototypes.html): answer beside each link
        var wrap = document.createElement('div');
        a.parentNode.insertBefore(wrap, a.nextSibling);
        var href = a.getAttribute('href');
        add(href, text(a.querySelector('b')), wrap, true, false, href.indexOf('prototype-') === 0 ? href : '');
      });
    }
    if (!targets.length) {
      // a prototype: one answer for the whole page, in a floating box
      var box = document.createElement('div');
      box.className = 'ri-float';
      var head = document.createElement('h4');
      head.textContent = 'Your pick for this prototype';
      var fold = document.createElement('button');
      fold.type = 'button';
      fold.className = 'ri-fold';
      function setFold(closed) {
        box.classList.toggle('ri-closed', closed);
        fold.textContent = closed ? 'Open' : 'Fold away';
        fold.setAttribute('aria-expanded', String(!closed));
        try { sessionStorage.setItem('ri-fold', closed ? '1' : ''); } catch (e) { /* ignore */ }
      }
      fold.addEventListener('click', function () { setFold(!box.classList.contains('ri-closed')); });
      head.appendChild(fold);
      box.appendChild(head);
      document.body.appendChild(box);
      var wasClosed = '';
      try { wasClosed = sessionStorage.getItem('ri-fold') || ''; } catch (e) { /* ignore */ }
      setFold(wasClosed === '1');
      add('pick', document.title, box, true, true);
    }
  }

  function render(t) {
    var s = rec(t);
    var el = document.createElement('div');
    el.className = 'ri';
    if (t.bind) {
      var hint = document.createElement('div');
      hint.style.cssText = 'font-size:13px;color:#5b6763;margin-bottom:6px';
      hint.textContent = 'Shared with the prototype: an answer given there shows here, and the other way round.';
      el.appendChild(hint);
    }
    var row = document.createElement('div');
    row.className = 'ri-row';
    CHOICES.forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'ri-c';
      b.dataset.v = c[0];
      b.textContent = c[1];
      b.setAttribute('aria-pressed', String(s.a === c[0]));
      b.addEventListener('click', function () {
        var next = rec(t).a === c[0] ? '' : c[0];
        row.querySelectorAll('button.ri-c').forEach(function (x) {
          x.setAttribute('aria-pressed', String(x.dataset.v === next));
        });
        put(t, { a: next });
      });
      row.appendChild(b);
    });
    var o = null;
    if (t.wantsOption) {
      var lab = document.createElement('label');
      lab.className = 'ri-opt';
      lab.appendChild(document.createTextNode('Option I pick'));
      o = document.createElement('input');
      o.className = 'ri-o';
      o.type = 'text';
      o.inputMode = 'numeric';
      o.placeholder = 'no.';
      o.value = s.opt || '';
      o.addEventListener('input', function () {
        put(t, { opt: o.value.trim() });
      });
      lab.appendChild(o);
      row.appendChild(lab);
    }
    el.appendChild(row);
    var n = document.createElement('textarea');
    n.className = 'ri-n';
    n.placeholder = 'Your thoughts (optional)';
    n.value = s.note || '';
    n.addEventListener('input', function () {
      put(t, { note: n.value });
    });
    // keep typing in the note from driving a prototype's own keyboard shortcuts
    ['keydown', 'keyup', 'keypress'].forEach(function (ev) {
      el.addEventListener(ev, function (e) { e.stopPropagation(); });
    });
    el.appendChild(n);
    t.host.appendChild(el);
    // called when the window regains focus or another page saves: show what is stored now
    t.sync = function () {
      var r = rec(t);
      row.querySelectorAll('button.ri-c').forEach(function (x) {
        x.setAttribute('aria-pressed', String(x.dataset.v === (r.a || '')));
      });
      if (o && document.activeElement !== o) o.value = r.opt || '';
      if (document.activeElement !== n) n.value = r.note || '';
    };
  }

  function answered(s) { return !!(s && (s.a || s.opt || (s.note && s.note.trim()))); }

  function lines(file, st, order) {
    var ids = order || Object.keys(st);
    var out = [];
    ids.forEach(function (id) {
      var s = st[id];
      if (!answered(s)) return;
      var bits = [];
      if (s.a) bits.push(s.a);
      if (s.opt) bits.push('option ' + s.opt);
      var line = (id === 'pick' ? 'pick' : id) + ': ' + (bits.join(', ') || 'note');
      if (s.note && s.note.trim()) line += ' | ' + s.note.trim().replace(/\s*\n\s*/g, ' / ');
      out.push(line);
    });
    return out.length ? ['== ' + file + ' =='].concat(out) : [];
  }

  function thisPage() {
    var view = {};
    var order = [];
    targets.forEach(function (t) {
      var label = t.bind && t.bind !== t.id ? t.id + ' (' + t.bind + ')' : t.id;
      view[label] = rec(t);
      order.push(label);
    });
    return lines(page, view, order).join('\n');
  }
  function everyPage() {
    var keys = [];
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k && k.indexOf(PREFIX) === 0) keys.push(k);
      }
    } catch (e) { /* no storage */ }
    keys.sort();
    var blocks = [];
    keys.forEach(function (k) {
      var l = lines(k.slice(PREFIX.length), k === KEY ? state : read(k));
      if (l.length) blocks.push(l.join('\n'));
    });
    return blocks.join('\n\n');
  }

  var bar = document.createElement('div');
  bar.className = 'ri-bar';
  var count = document.createElement('b');
  var msg = document.createElement('span');
  msg.className = 'ri-msg';
  var out = document.createElement('div');
  out.className = 'ri-out';
  var outText = document.createElement('textarea');
  outText.readOnly = true;
  out.appendChild(outText);

  function copy(getText, what) {
    var t = getText();
    outText.value = t || '(nothing answered yet)';
    out.style.display = 'block';
    outText.focus();
    outText.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    if (navigator.clipboard && navigator.clipboard.writeText && t) {
      navigator.clipboard.writeText(t).then(function () { msg.textContent = what + ' copied. Paste it into the chat.'; }, function () {});
    }
    msg.textContent = ok && t ? what + ' copied. Paste it into the chat.' : 'Select the text above and copy it.';
  }
  function button(label, main, fn) {
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    if (main) b.className = 'ri-main';
    b.addEventListener('click', fn);
    return b;
  }

  function refresh() {
    if (isIndex) {
      var pages = 0;
      var total = 0;
      document.querySelectorAll('a.item[href]').forEach(function (a) {
        var st = read(PREFIX + a.getAttribute('href'));
        var n = Object.keys(st).filter(function (id) { return answered(st[id]); }).length;
        var tag = a.querySelector('.ri-count');
        if (!tag) { tag = document.createElement('span'); tag.className = 'ri-count'; a.querySelector('b').appendChild(tag); }
        tag.textContent = n ? n + ' answered' : '';
        if (n) { pages++; total += n; }
      });
      count.textContent = total + ' answers on ' + pages + ' pages';
    } else {
      var done = targets.filter(function (t) { return answered(rec(t)); }).length;
      count.textContent = done + ' of ' + targets.length + ' answered';
    }
  }
  function resync() {
    state = read(KEY);
    targets.forEach(function (t) { if (t.sync) t.sync(); });
    refresh();
  }

  // Answers given on an item before it was linked to its prototype: carry them over once.
  targets.forEach(function (t) {
    var own = t.bind ? state[t.id] : null;
    if (!own || !answered(own)) return;
    var st = read(PREFIX + t.bind);
    if (!answered(st.pick)) {
      st.pick = own;
      try { localStorage.setItem(PREFIX + t.bind, JSON.stringify(st)); } catch (e) { /* no storage */ }
    }
    delete state[t.id];
    write(state);
  });
  targets.forEach(render);
  bar.appendChild(count);
  if (!isIndex) bar.appendChild(button('Copy this page’s answers', true, function () { copy(thisPage, 'This page’s answers'); }));
  bar.appendChild(button('Copy answers from every page', isIndex, function () { copy(everyPage, 'Every page’s answers'); }));
  bar.appendChild(button('Hide text', false, function () { out.style.display = 'none'; }));
  if (!isIndex) {
    var back = document.createElement('a');
    back.href = 'index.html';
    back.textContent = 'Back to the index';
    bar.appendChild(back);
  }
  bar.appendChild(msg);
  document.body.appendChild(out);
  document.body.appendChild(bar);
  refresh();
  window.addEventListener('focus', resync);
  window.addEventListener('pageshow', resync);
  window.addEventListener('storage', resync);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) resync(); });
})();
