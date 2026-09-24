(function () {
  'use strict';

  var el = function (id) { return document.getElementById(id); };
  var dcEl = el('grpg-deep-chat');
  var state = { consented: dcEl.getAttribute('data-consented') === 'true' };
  var current = { conversationId: null };

  var els = {
    consent: el('grpg-consent'),
    shell: el('grpg-chat-shell'),
    threads: el('grpg-threads'),
    hint: el('grpg-hint'),
    newThread: el('grpg-new-thread'),
    revoke: el('grpg-revoke'),
    grant: el('grpg-consent-grant'),
    provider: el('grpg-provider'),
  };

  function hint(msg) { els.hint.textContent = msg || ''; }

  function fetchJson(url, options) {
    return fetch(url, options).then(function (res) {
      if (res.status === 204) return { ok: true, data: null };
      return res.json().then(function (d) { return { ok: res.ok, data: d }; }).catch(function () {
        return { ok: res.ok, data: { msg: 'Unexpected response' } };
      });
    }).catch(function () { return { ok: false, data: { msg: 'Network error' } }; });
  }

  // ── Consent ────────────────────────────────────────────────────────────────
  function applyConsentUi() {
    els.consent.style.display = state.consented ? 'none' : 'block';
    els.shell.style.display = state.consented ? 'grid' : 'none';
    if (!state.consented) {
      els.threads.innerHTML = '';
      setIntro(true);
      return;
    }
    loadThreads();
    renderSidePanel();
  }

  els.grant.addEventListener('click', function () {
    fetchJson('/api/ai-consent', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consented: true })
    }).then(function (r) {
      if (r.ok) { state.consented = true; applyConsentUi(); hint(''); }
      else hint((r.data && r.data.msg) || 'Could not enable AI Chat.');
    });
  });

  els.revoke.addEventListener('click', function () {
    if (!window.confirm('Disable AI Chat? Your history is kept, but no more messages will be sent.')) return;
    fetchJson('/api/ai-consent', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consented: false })
    }).then(function (r) {
      if (r.ok) { state.consented = false; current.conversationId = null; applyConsentUi(); }
      else hint((r.data && r.data.msg) || 'Could not disable.');
    });
  });

  els.provider.addEventListener('click', function () {
    hint('Checking provider…');
    fetchJson('/api/judge/health').then(function (r) {
      if (r.ok) hint('Provider reachable.');
      else hint((r.data && r.data.detail) || 'Provider currently unreachable.');
    });
  });

  // ── Deep Chat branding ────────────────────────────────────────────────────
  // Single, tunable place for the chat look. Colors are `var(--chat-*, hex)`
  // pairs so every theme (garden-rpg / default) styles the chat automatically
  // (custom properties pierce Deep Chat's shadow root).
  var CHAT_THEME = {
    // Surfaces
    chatBg: 'var(--chat-panel, #151820)',
    inputBg: 'var(--chat-input-bg, #1a1d26)',
    border: 'var(--chat-border, #232733)',
    borderSoft: 'var(--chat-border-soft, #1c2029)',
    // Text
    text: 'var(--chat-text, #e4e6eb)',
    textDim: 'var(--chat-text-dim, #9aa0ad)',
    textFaint: 'var(--chat-text-faint, #6b7280)',
    // Bubbles
    accent: 'var(--chat-teal, #14b8c4)',
    accentHover: 'var(--chat-teal-dim, #0ea5b8)',
    userText: 'var(--chat-user-text, #06232a)',
    aiBubble: 'var(--chat-ai-bubble, #1e2230)',
    radius: '14px',
    bubblePad: '12px 16px',
    bubbleMaxWidth: '820px',
    // Scrollbar / markdown
    scrollbar: 'var(--chat-scrollbar, #252a36)',
    scrollbarHover: 'var(--chat-scrollbar-hover, #2e3442)',
    // Name / avatar visibility (preview shows plain bubbles)
    showNames: false,
    showAvatars: false,
    aiAvatar: dcEl.getAttribute('data-ai-avatar') || '',
    userAvatar: '/static/vendor/deep-chat/person-avatar.png',
    userPlaceholder: 'Message your companion…',
  };

  function applyChatBranding() {
    var t = CHAT_THEME;

    dcEl.chatStyle = {
      backgroundColor: t.chatBg,
      width: '100%',
      height: '100%',
      borderRadius: '0',
      fontFamily: 'var(--font-body, Inter, sans-serif)',
      fontSize: '14px',
    };

    dcEl.messageStyles = {
      default: {
        shared: {
          bubble: {
            color: t.text,
            fontSize: '14px',
            lineHeight: '1.55',
            padding: t.bubblePad,
            maxWidth: t.bubbleMaxWidth,
          },
        },
        ai: {
          bubble: { backgroundColor: t.aiBubble, borderRadius: t.radius + ' ' + t.radius + ' ' + t.radius + ' 4px' },
        },
        user: {
          bubble: { backgroundColor: t.accent, color: t.userText, borderRadius: t.radius + ' ' + t.radius + ' 4px ' + t.radius },
        },
      },
      intro: {
        bubble: { backgroundColor: 'transparent', color: t.textFaint, borderRadius: '0', padding: '24px 8px' },
      },
      error: {
        bubble: { backgroundColor: '#3a1f1c', color: '#f0b4ab', borderRadius: t.radius + ' ' + t.radius + ' ' + t.radius + ' 4px' },
      },
    };

    dcEl.inputAreaStyle = {
      backgroundColor: 'transparent',
      borderTop: '1px solid ' + t.borderSoft,
      padding: '14px',
    };

    dcEl.textInput = {
      styles: {
        container: {
          backgroundColor: t.inputBg,
          border: '1px solid ' + t.border,
          borderRadius: '999px',
          padding: '4px 12px',
          minHeight: '46px',
        },
        focus: { border: '1px solid ' + t.accent },
        text: { color: t.text, fontSize: '14px' },
      },
      placeholder: { text: t.userPlaceholder, style: { color: t.textFaint } },
    };

    dcEl.submitButtonStyles = {
      submit: {
        container: {
          default: { backgroundColor: t.accent, borderRadius: '50%', width: '38px', height: '38px' },
          hover: { backgroundColor: t.accentHover },
          click: { backgroundColor: t.accentHover },
        },
        svg: { styles: { default: { fill: t.userText } } },
      },
      alwaysEnabled: true,
    };

    dcEl.names = t.showNames;
    if (t.showAvatars) {
      dcEl.avatars = { ai: t.aiAvatar, user: t.userAvatar };
    }

    dcEl.auxiliaryStyle = [
      '::-webkit-scrollbar{width:9px;height:9px}',
      '::-webkit-scrollbar-track{background:transparent}',
      '::-webkit-scrollbar-thumb{background:' + t.scrollbar + ';border-radius:5px}',
      '::-webkit-scrollbar-thumb:hover{background:' + t.scrollbarHover + '}',
      'a{color:' + t.accent + ';text-decoration:none}',
      'a:hover{text-decoration:underline}',
      'pre,code{background:' + t.inputBg + ';border:1px solid ' + t.borderSoft + ';border-radius:8px}',
      'blockquote{border-left:3px solid ' + t.accent + ';padding-left:12px;color:' + t.textDim + '}',
      'p{margin:0 0 8px}',
    ].join('');
  }

  function dcRequest(id) {
    return {
      url: '/api/chat/conversations/' + id + '/messages',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
      credentials: 'same-origin',
      stream: true,
    };
  }

  function setIntro(initial) {
    var dc = dcEl;
    dc.connect = null;
    dc.disabled = true;
    dc.history = [];
    if (initial) {
      dc.introMessage = {
        text: 'Welcome! Pick a conversation from the left or start a new one.',
      };
    } else {
      dc.introMessage = null;
    }
  }

  function mountThread(id) {
    current.conversationId = id;
    renderThreadActive();
    hint('');
    clearSetupBanner();
    dcEl.history = [];
    fetchJson('/api/chat/conversations/' + id + '/messages').then(function (r) {
      if (!r.ok) { hint((r.data && r.data.msg) || 'Could not load messages.'); return; }
      var history = (r.data.messages || []).map(function (m) {
        return { role: m.role === 'user' ? 'user' : 'ai', text: m.content || '' };
      });
      dcEl.history = history;
      dcEl.connect = dcRequest(id);
      dcEl.disabled = false;
      dcEl.introMessage = null;
    });
  }

  function selectThread(id) {
    mountThread(id);
  }

  // Deep Chat adds a "Connect to any API…" onboarding message at construction
  // (before this script runs). It only ever coexists with real history once a
  // conversation is mounted, so it is safe to wipe it while the message list
  // holds nothing but that banner — and never otherwise.
  function clearSetupBanner() {
    try {
      if (!dcEl.getMessages) return;
      var msgs = dcEl.getMessages() || [];
      var isBanner = function (m) {
        return typeof m.text === 'string' && m.text.indexOf('Connect to any API') !== -1;
      };
      if (msgs.length && msgs.every(isBanner)) dcEl.clearMessages();
    } catch (e) { /* irreversible on purpose */ }
  }

  // ── Threads ────────────────────────────────────────────────────────────────
  function threadRow(c) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'grpg-chat-thread' + (c.id === current.conversationId ? ' active' : '');
    btn.dataset.id = String(c.id);

    var title = document.createElement('span');
    title.className = 'grpg-chat-thread-title';
    title.textContent = c.title || ('Chat #' + c.id);
    btn.appendChild(title);

    var count = document.createElement('span');
    count.className = 'grpg-chat-thread-count';
    count.textContent = c.message_count || 0;
    btn.appendChild(count);

    btn.addEventListener('click', function () { selectThread(c.id); });
    btn.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      threadMenu(c);
    });
    return btn;
  }

  function threadMenu(c) {
    var action = window.prompt(
      'Conversation: ' + (c.title || ('Chat #' + c.id)) + '\n\n' +
      'Rename: type a new title.\nDelete: type DELETE.'
    );
    if (!action) return;
    if (action.trim().toUpperCase() === 'DELETE') {
      if (!window.confirm('Delete this conversation and its full message history?')) return;
      fetchJson('/api/chat/conversations/' + c.id, { method: 'DELETE' }).then(function (r) {
        if (r.ok) {
          if (current.conversationId === c.id) { current.conversationId = null; setIntro(false); showNoConversation(); }
          loadThreads();
        } else hint((r.data && r.data.msg) || 'Could not delete.');
      });
      return;
    }
    fetchJson('/api/chat/conversations/' + c.id, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: action.trim().slice(0, 200) })
    }).then(function (r) { if (r.ok) loadThreads(); else hint((r.data && r.data.msg) || 'Could not rename.'); });
  }

  function showNoConversation() {
    els.threads.innerHTML = '';
    var empty = document.createElement('div');
    empty.className = 'grpg-chat-sidebar-empty';
    empty.textContent = 'No conversations yet.';
    els.threads.appendChild(empty);
  }

  function loadThreads() {
    fetchJson('/api/chat/conversations').then(function (r) {
      els.threads.innerHTML = '';
      if (!r.ok) { hint((r.data && r.data.msg) || 'Could not load conversations.'); return; }
      var list = r.data.conversations || [];
      if (!list.length) { showNoConversation(); return; }
      list.forEach(function (c) { els.threads.appendChild(threadRow(c)); });
      // Open the most recent conversation by default so a live `connect` is
      // active instead of Deep Chat's onboarding banner.
      if (current.conversationId === null && state.consented) selectThread(list[0].id);
    });
  }

  function renderThreadActive() {
    Array.prototype.forEach.call(els.threads.children, function (child) {
      if (child.classList && child.classList.contains('grpg-chat-thread')) {
        child.classList.toggle('active', child.dataset.id === String(current.conversationId));
      }
    });
  }

  els.newThread.addEventListener('click', function () {
    fetchJson('/api/chat/conversations', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '' })
    }).then(function (r) {
      if (!r.ok) { hint((r.data && r.data.msg) || 'Could not create conversation.'); return; }
      selectThread(r.data.id);
    });
  });

  // ── Right context panel ───────────────────────────────────────────────────
  var DONE_STATUS = ['DONE', 'LATE', 'PARTIAL'];

  function renderSidePanel() {
    Promise.all([
      fetchJson('/api/missions/today'),
      fetchJson('/api/system-judge/latest'),
    ]).then(function (results) {
      var missions = (results[0].data && results[0].data.missions) || [];
      var profile = (results[0].data && results[0].data.profile) || {};
      var judge = results[1].data || {};

      // XP card
      if (profile && profile.level) {
        el('grpg-cp-level').innerHTML = 'Level <b>' + profile.level + '</b>';
        el('grpg-cp-streak').textContent = '\uD83D\uDD25 ' + (profile.streak || 0) + '-day streak';
        el('grpg-cp-xp-fill').style.width = Math.max(0, Math.min(100, profile.xp_progress_pct || 0)) + '%';
        el('grpg-cp-xp-label').textContent = profile.next_level
          ? (profile.exp_to_next + ' XP to Level ' + profile.next_level)
          : 'Max level reached';
      }

      // Active quests + rest-of-day
      var remaining = missions.filter(function (m) { return m.status === 'ACTIVE'; });
      var done = missions.filter(function (m) { return DONE_STATUS.indexOf(m.status) !== -1; }).length;

      var qEl = el('grpg-cp-quests');
      qEl.innerHTML = '';
      if (remaining.length) {
        remaining.slice(0, 6).forEach(function (m) {
          var row = document.createElement('div');
          row.className = 'grpg-cp-quest';

          var check = document.createElement('div');
          check.className = 'grpg-cp-check';

          var text = document.createElement('div');
          text.className = 'grpg-cp-quest-text';
          var title = document.createElement('div');
          title.className = 'grpg-cp-quest-title';
          title.textContent = m.title || 'Task';
          var meta = document.createElement('div');
          meta.className = 'grpg-cp-quest-meta';
          meta.textContent = [m.start, m.duration ? (m.duration + ' min') : '', m.xp ? ('+' + m.xp + ' XP') : '']
            .filter(Boolean).join(' · ');

          text.appendChild(title);
          text.appendChild(meta);
          row.appendChild(check);
          row.appendChild(text);
          qEl.appendChild(row);
        });
      } else {
        qEl.innerHTML = '<div class="grpg-cp-empty">No pending quests. Nice.</div>';
      }

      // Stats snapshot
      el('grpg-cp-done').textContent = done + '/' + (missions.length || 0);
      el('grpg-cp-missed').textContent = judge.missed_count || 0;

      // Rest of your day
      var ttEl = el('grpg-cp-tt');
      ttEl.innerHTML = '';
      var upcoming = remaining
        .filter(function (m) { return m.start; })
        .sort(function (a, b) { return a.start < b.start ? -1 : (a.start > b.start ? 1 : 0); });
      if (upcoming.length) {
        upcoming.slice(0, 6).forEach(function (m) {
          var row = document.createElement('div');
          row.className = 'grpg-cp-tt-row';
          var t = document.createElement('div');
          t.className = 'grpg-cp-tt-time';
          t.textContent = m.start;
          var dot = document.createElement('div');
          dot.className = 'grpg-cp-tt-dot';
          var lbl = document.createElement('div');
          lbl.className = 'grpg-cp-tt-label';
          lbl.textContent = m.title || '';
          row.appendChild(t);
          row.appendChild(dot);
          row.appendChild(lbl);
          ttEl.appendChild(row);
        });
      } else {
        ttEl.innerHTML = '<div class="grpg-cp-empty">Nothing scheduled for the rest of today.</div>';
      }
    });
  }

  // Refresh sidebar counts and the context panel after each delivered message.
  var refreshDebounce = null;
  dcEl.addEventListener('new-message', function () {
    if (refreshDebounce) clearTimeout(refreshDebounce);
    refreshDebounce = setTimeout(function () {
      if (state.consented && els.shell.style.display !== 'none') {
        loadThreads();
        renderSidePanel();
      }
    }, 600);
  });

  dcEl.addEventListener('error', function (e) {
    if (e && e.detail && e.detail.text) hint('Error: ' + e.detail.text);
  });

  // ── Init ───────────────────────────────────────────────────────────────────
  applyChatBranding();
  applyConsentUi();
  if (state.consented) {
    window.setTimeout(function () {
      if (els.shell.style.display !== 'none' && current.conversationId === null) clearSetupBanner();
    }, 1500);
  }
})();