/**
 * Smart Notepad — script.js
 * Complete vanilla JS (no jQuery, no external libs)
 */

/* ============================================================
   1. THEME MANAGER
   ============================================================ */
const ThemeManager = (() => {
  const STORAGE_KEY = 'theme';
  const THEMES = { LIGHT: 'light', DARK: 'dark', SYSTEM: 'system' };

  function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function applyTheme(preference) {
    const effective = preference === THEMES.SYSTEM ? getSystemTheme() : preference;
    document.body.setAttribute('data-theme', effective);
    updateToggleIcon(effective);
    updateThemeButtons(preference);
  }

  function updateToggleIcon(effective) {
    const btn = document.getElementById('darkModeToggle');
    if (!btn) return;
    const sun  = btn.querySelector('.icon-sun');
    const moon = btn.querySelector('.icon-moon');
    if (sun && moon) {
      if (effective === 'dark') {
        sun.style.display  = 'inline';
        moon.style.display = 'none';
        btn.setAttribute('title', 'Switch to light mode');
      } else {
        sun.style.display  = 'none';
        moon.style.display = 'inline';
        btn.setAttribute('title', 'Switch to dark mode');
      }
    }
  }

  function updateThemeButtons(preference) {
    document.querySelectorAll('.theme-btn[data-theme-value]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.themeValue === preference);
    });
  }

  function getCurrentPreference() {
    return localStorage.getItem(STORAGE_KEY) || THEMES.SYSTEM;
  }

  function setTheme(preference) {
    localStorage.setItem(STORAGE_KEY, preference);
    applyTheme(preference);
  }

  function toggle() {
    const current = document.body.getAttribute('data-theme') || 'light';
    setTheme(current === 'dark' ? THEMES.LIGHT : THEMES.DARK);
  }

  function init() {
    // Apply saved preference immediately (before DOMContentLoaded to avoid flash)
    const pref = getCurrentPreference();
    applyTheme(pref);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (getCurrentPreference() === THEMES.SYSTEM) {
        applyTheme(THEMES.SYSTEM);
      }
    });
  }

  return { init, toggle, setTheme, getCurrentPreference };
})();

// Apply theme as early as possible
ThemeManager.init();

/* ============================================================
   HELPERS
   ============================================================ */

/**
 * Debounce: delay execution until `wait` ms after last call.
 */
function debounce(fn, wait) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), wait);
  };
}

/**
 * Trigger a file download from a Blob.
 */
function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 150);
}

/**
 * Show a temporary Bootstrap-style alert at the top of flash container.
 */
function showAlert(message, type = 'info', duration = 4000) {
  let container = document.querySelector('.flash-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
  }
  const alert = document.createElement('div');
  alert.className = `alert alert-${type} alert-dismissible fade show`;
  alert.role = 'alert';
  alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
  container.appendChild(alert);
  if (duration > 0) {
    setTimeout(() => {
      if (alert && alert.parentNode) {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
      }
    }, duration);
  }
}

/**
 * Escape HTML to prevent XSS when inserting untrusted text as innerHTML.
 */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

/**
 * Format a date string into a readable relative/absolute label.
 */
function formatDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7)   return `${days}d ago`;
  return date.toLocaleDateString();
}

/**
 * Strip HTML tags to get plain-text preview.
 */
function stripHtml(html) {
  const tmp = document.createElement('div');
  tmp.innerHTML = html || '';
  return tmp.textContent || tmp.innerText || '';
}

/* ============================================================
   2. NOTES LOADER (dashboard — index page)
   ============================================================ */
const NotesLoader = (() => {
  const GRID_ID = 'notes-grid';
  const COUNT_ID = 'total-notes';

  function buildNoteCard(note) {
    const preview = stripHtml(note.content).slice(0, 120) + (note.content && stripHtml(note.content).length > 120 ? '…' : '');
    return `
      <div class="note-card" data-note-id="${note.id}" id="card-${note.id}">
        <div class="note-card-header">
          <h3 class="note-card-title">${escapeHtml(note.heading || 'Untitled')}</h3>
          <div class="note-card-timestamps">
            <span><i class="fa-regular fa-clock"></i> Updated ${escapeHtml(formatDate(note.updated_at))}</span>
            <span><i class="fa-regular fa-calendar"></i> Created ${escapeHtml(formatDate(note.created_at))}</span>
          </div>
        </div>
        <div class="note-card-body">
          <p class="note-card-preview">${escapeHtml(preview) || '<em class="text-muted">No content</em>'}</p>
        </div>
        <div class="note-card-footer">
          <a href="/note/${note.id}" class="btn btn-primary btn-sm">
            <i class="fa fa-pencil"></i> Edit
          </a>
          <button class="btn btn-danger btn-sm btn-delete-card"
                  data-note-id="${note.id}"
                  data-note-heading="${escapeHtml(note.heading || 'Untitled')}"
                  data-bs-toggle="modal"
                  data-bs-target="#deleteModal">
            <i class="fa fa-trash"></i> Delete
          </button>
          <a href="/api/notes/${note.id}/export" class="btn btn-outline-secondary btn-sm"
             target="_blank" rel="noopener">
            <i class="fa fa-download"></i> Export
          </a>
        </div>
      </div>`;
  }

  function buildEmptyState() {
    return `<div class="empty-state" id="empty-state">
      <span class="empty-emoji">📝</span>
      <h4>No notes yet</h4>
      <p>Create your first note to get started!</p>
      <a href="/note/new" class="btn btn-primary btn-new-note">
        <i class="fa fa-plus"></i> Create a Note
      </a>
    </div>`;
  }

  function renderSkeleton(grid) {
    grid.innerHTML = Array.from({ length: 6 }, () =>
      `<div class="skeleton skeleton-card"></div>`
    ).join('');
  }

  async function loadNotes(sort = 'updated') {
    const grid = document.getElementById(GRID_ID);
    if (!grid) return;

    renderSkeleton(grid);

    try {
      const res = await fetch(`/api/notes?sort=${encodeURIComponent(sort)}`);
      if (!res.ok) throw new Error('Failed to load notes');
      const notes = await res.json();

      // Update total count
      const countEl = document.getElementById(COUNT_ID);
      if (countEl) countEl.textContent = notes.length;

      // Render
      if (notes.length === 0) {
        grid.innerHTML = buildEmptyState();
      } else {
        grid.innerHTML = notes.map(buildNoteCard).join('');
        // Re-attach delete listeners after render
        attachDashboardDeleteListeners();
      }
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">
        <span class="empty-emoji">⚠️</span>
        <h4>Could not load notes</h4>
        <p>${escapeHtml(err.message)}</p>
      </div>`;
    }
  }

  function init() {
    const grid = document.getElementById(GRID_ID);
    if (!grid) return; // Not on dashboard

    // Initial load
    const sortEl = document.getElementById('sort-select');
    const sort = sortEl ? sortEl.value : 'updated';
    loadNotes(sort);

    // Sort dropdown
    if (sortEl) {
      sortEl.addEventListener('change', () => loadNotes(sortEl.value));
    }
  }

  return { init, loadNotes };
})();

/* ============================================================
   3. SEARCH
   ============================================================ */
const SearchManager = (() => {
  // ---- Navbar search ----
  function initNavbarSearch() {
    const input    = document.getElementById('navbar-search');
    const dropdown = document.getElementById('search-dropdown');
    if (!input || !dropdown) return;

    const doSearch = debounce(async (q) => {
      if (!q.trim()) { dropdown.classList.remove('show'); return; }
      try {
        const res = await fetch(`/api/notes/search?q=${encodeURIComponent(q)}`);
        const notes = await res.json();
        renderNavbarDropdown(notes, dropdown, q);
      } catch {
        dropdown.innerHTML = '<div class="search-no-results">⚠️ Search failed</div>';
        dropdown.classList.add('show');
      }
    }, 300);

    input.addEventListener('input', () => doSearch(input.value));

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') dropdown.classList.remove('show');
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (!input.closest('.navbar-search-wrapper').contains(e.target)) {
        dropdown.classList.remove('show');
      }
    });
  }

  function renderNavbarDropdown(notes, dropdown, q) {
    if (notes.length === 0) {
      dropdown.innerHTML = `<div class="search-no-results">🔍 No results for "<strong>${escapeHtml(q)}</strong>"</div>`;
    } else {
      dropdown.innerHTML = notes.slice(0, 8).map(n => `
        <div class="search-result-item" data-href="/note/${n.id}" role="button" tabindex="0">
          <div class="result-title">${escapeHtml(n.heading || 'Untitled')}</div>
          <div class="result-preview">${escapeHtml(stripHtml(n.content).slice(0, 80))}</div>
        </div>`).join('');

      dropdown.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => { window.location.href = item.dataset.href; });
        item.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') window.location.href = item.dataset.href;
        });
      });
    }
    dropdown.classList.add('show');
  }

  // ---- Dashboard search ----
  function initDashboardSearch() {
    const input     = document.getElementById('dashboard-search');
    const grid      = document.getElementById('notes-grid');
    const resultsEl = document.getElementById('search-results');
    if (!input || !grid) return;

    const doSearch = debounce(async (q) => {
      if (!q.trim()) {
        // Restore normal grid
        const sortEl = document.getElementById('sort-select');
        NotesLoader.loadNotes(sortEl ? sortEl.value : 'updated');
        if (resultsEl) resultsEl.classList.add('d-none');
        return;
      }
      try {
        const res = await fetch(`/api/notes/search?q=${encodeURIComponent(q)}`);
        const notes = await res.json();
        if (resultsEl) {
          resultsEl.classList.remove('d-none');
          resultsEl.innerHTML = `<p class="text-muted-sm mb-2">Found ${notes.length} result(s) for "<strong>${escapeHtml(q)}</strong>"</p>`;
        }

        if (notes.length === 0) {
          grid.innerHTML = `<div class="empty-state">
            <span class="empty-emoji">🔍</span>
            <h4>No results</h4>
            <p>No notes match "<strong>${escapeHtml(q)}</strong>"</p>
          </div>`;
        } else {
          grid.innerHTML = notes.map(n => {
            const preview = stripHtml(n.content).slice(0, 120);
            return `<div class="note-card" data-note-id="${n.id}" id="card-${n.id}">
              <div class="note-card-header">
                <h3 class="note-card-title">${escapeHtml(n.heading || 'Untitled')}</h3>
                <div class="note-card-timestamps">
                  <span><i class="fa-regular fa-clock"></i> ${escapeHtml(formatDate(n.updated_at))}</span>
                </div>
              </div>
              <div class="note-card-body">
                <p class="note-card-preview">${escapeHtml(preview)}</p>
              </div>
              <div class="note-card-footer">
                <a href="/note/${n.id}" class="btn btn-primary btn-sm"><i class="fa fa-pencil"></i> Edit</a>
                <button class="btn btn-danger btn-sm btn-delete-card"
                        data-note-id="${n.id}"
                        data-note-heading="${escapeHtml(n.heading || 'Untitled')}"
                        data-bs-toggle="modal"
                        data-bs-target="#deleteModal">
                  <i class="fa fa-trash"></i> Delete
                </button>
              </div>
            </div>`;
          }).join('');
          attachDashboardDeleteListeners();
        }
      } catch {
        grid.innerHTML = '<div class="empty-state"><span class="empty-emoji">⚠️</span><h4>Search failed</h4></div>';
      }
    }, 300);

    input.addEventListener('input', () => doSearch(input.value));
  }

  function init() {
    initNavbarSearch();
    initDashboardSearch();
  }

  return { init };
})();

/* ============================================================
   4. NOTE EDITOR
   ============================================================ */
const NoteEditor = (() => {
  let currentNoteId = null;
  let autoSaveTimer = null;

  function init() {
    const editorContent = document.getElementById('editor-content');
    if (!editorContent) return; // Not on editor page

    // Read note id from data attribute (or hidden input)
    const noteIdEl = document.getElementById('note-id');
    if (noteIdEl && noteIdEl.value) {
      currentNoteId = parseInt(noteIdEl.value, 10) || null;
    }

    // Load content from data attrs on the editor element itself
    const headingInput = document.getElementById('note-heading');
    if (headingInput && headingInput.dataset.initialValue) {
      headingInput.value = headingInput.dataset.initialValue;
    }
    if (editorContent.dataset.initialContent) {
      editorContent.innerHTML = editorContent.dataset.initialContent;
    }

    // Sync to hidden textarea
    const hiddenTextarea = document.getElementById('editor-hidden-content');

    function syncToTextarea() {
      if (hiddenTextarea) hiddenTextarea.value = editorContent.innerHTML;
    }

    // Trigger auto-save on input
    editorContent.addEventListener('input', () => {
      syncToTextarea();
      scheduleAutoSave();
    });

    if (headingInput) {
      headingInput.addEventListener('input', () => scheduleAutoSave());
    }

    // Toolbar buttons
    initToolbar(editorContent);

    // Export button
    const exportBtn = document.getElementById('btn-export');
    if (exportBtn) {
      exportBtn.addEventListener('click', handleExport);
    }

    // Delete button (editor page)
    const deleteBtn = document.getElementById('btn-delete-note');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => {
        if (currentNoteId) {
          const modal = document.getElementById('deleteModal');
          if (modal) {
            const headingEl = document.getElementById('delete-note-heading');
            const hInput    = document.getElementById('note-heading');
            if (headingEl && hInput) headingEl.textContent = hInput.value || 'Untitled';
            bootstrap.Modal.getOrCreateInstance(modal).show();
          }
        }
      });
    }

    // Confirm delete
    const confirmDeleteBtn = document.getElementById('btn-confirm-delete');
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', handleDelete);
    }

    // Initial sync
    syncToTextarea();
  }

  /* ---- Toolbar ---- */
  function initToolbar(editorContent) {
    document.querySelectorAll('.toolbar-btn[data-command]').forEach(btn => {
      btn.addEventListener('mousedown', (e) => {
        e.preventDefault(); // Prevent losing selection
        const cmd   = btn.dataset.command;
        const value = btn.dataset.value || null;
        execEditorCommand(cmd, value, editorContent);
        updateActiveButtons();
      });
    });

    // Update active state on selection change
    editorContent.addEventListener('keyup', updateActiveButtons);
    editorContent.addEventListener('mouseup', updateActiveButtons);
    document.addEventListener('selectionchange', () => {
      if (document.activeElement === editorContent) updateActiveButtons();
    });
  }

  function execEditorCommand(cmd, value, editor) {
    editor.focus();
    if (['h1', 'h2', 'h3'].includes(cmd)) {
      document.execCommand('formatBlock', false, cmd);
    } else if (cmd === 'p') {
      document.execCommand('formatBlock', false, 'p');
    } else {
      document.execCommand(cmd, false, value);
    }
    scheduleAutoSave();
  }

  function updateActiveButtons() {
    const formatCommands = ['bold', 'italic', 'underline', 'strikeThrough',
                            'insertUnorderedList', 'insertOrderedList'];
    formatCommands.forEach(cmd => {
      const isActive = document.queryCommandState(cmd);
      document.querySelectorAll(`.toolbar-btn[data-command="${cmd}"]`).forEach(btn => {
        btn.classList.toggle('active', isActive);
      });
    });

    // Heading detection
    const block = document.queryCommandValue('formatBlock').toLowerCase();
    ['h1', 'h2', 'h3', 'p'].forEach(tag => {
      document.querySelectorAll(`.toolbar-btn[data-command="${tag}"]`).forEach(btn => {
        btn.classList.toggle('active', block === tag);
      });
    });
  }

  /* ---- Auto-save ---- */
  function scheduleAutoSave() {
    clearTimeout(autoSaveTimer);
    setAutoSaveStatus('saving');
    autoSaveTimer = setTimeout(performAutoSave, 2000);
  }

  function setAutoSaveStatus(status, timestamp) {
    const indicator = document.querySelector('.autosave-indicator');
    const textEl    = indicator ? indicator.querySelector('.autosave-text') : null;
    if (!indicator || !textEl) return;

    indicator.className = `autosave-indicator ${status}`;
    if (status === 'saving') {
      textEl.textContent = 'Saving…';
    } else if (status === 'saved') {
      const timeStr = timestamp ? ` at ${timestamp}` : '';
      textEl.textContent = `Saved ✓${timeStr}`;
    } else if (status === 'error') {
      textEl.textContent = 'Save failed';
    } else {
      textEl.textContent = 'All changes saved';
    }
  }

  async function performAutoSave() {
    const headingInput  = document.getElementById('note-heading');
    const editorContent = document.getElementById('editor-content');
    if (!editorContent) return;

    const heading = headingInput ? headingInput.value.trim() : 'Untitled';
    const content = editorContent.innerHTML;

    try {
      let res, data;
      if (currentNoteId) {
        res = await fetch(`/api/notes/${currentNoteId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ heading, content }),
        });
      } else {
        res = await fetch('/api/notes', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ heading, content }),
        });
      }

      if (!res.ok) throw new Error(await res.text());
      data = await res.json();

      // If new note, update ID and URL
      if (!currentNoteId && data.id) {
        currentNoteId = data.id;
        const noteIdEl = document.getElementById('note-id');
        if (noteIdEl) noteIdEl.value = data.id;
        history.pushState({ noteId: data.id }, '', `/note/${data.id}`);
      }

      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      setAutoSaveStatus('saved', timeStr);

      // Revert to idle after 3s
      setTimeout(() => setAutoSaveStatus('idle'), 3000);
    } catch (err) {
      setAutoSaveStatus('error');
      console.error('Auto-save failed:', err);
    }
  }

  /* ---- Export ---- */
  async function handleExport() {
    if (!currentNoteId) { showAlert('Save the note first before exporting.', 'warning'); return; }
    try {
      const res = await fetch(`/api/notes/${currentNoteId}/export`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition') || '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : `note-${currentNoteId}.txt`;
      triggerDownload(blob, filename);
    } catch (err) {
      showAlert('Export failed: ' + err.message, 'danger');
    }
  }

  /* ---- Delete ---- */
  async function handleDelete() {
    if (!currentNoteId) return;
    try {
      const res = await fetch(`/api/notes/${currentNoteId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      window.location.href = '/';
    } catch (err) {
      showAlert('Delete failed: ' + err.message, 'danger');
      const modal = document.getElementById('deleteModal');
      if (modal) bootstrap.Modal.getOrCreateInstance(modal).hide();
    }
  }

  return { init };
})();

/* ============================================================
   5. DELETE FROM DASHBOARD
   ============================================================ */

function attachDashboardDeleteListeners() {
  // Set up listeners for all dashboard delete buttons
  document.querySelectorAll('.btn-delete-card').forEach(btn => {
    // Remove existing listener to avoid duplicates
    btn.replaceWith(btn.cloneNode(true));
  });

  document.querySelectorAll('.btn-delete-card').forEach(btn => {
    btn.addEventListener('click', () => {
      const noteId      = btn.dataset.noteId;
      const noteHeading = btn.dataset.noteHeading;

      // Set info in modal
      const headingEl = document.getElementById('delete-note-heading');
      if (headingEl) headingEl.textContent = noteHeading;

      // Store id on confirm button
      const confirmBtn = document.getElementById('btn-confirm-delete');
      if (confirmBtn) confirmBtn.dataset.noteId = noteId;
    });
  });

  // Confirm delete button on dashboard
  const confirmBtn = document.getElementById('btn-confirm-delete');
  if (confirmBtn && !confirmBtn.dataset.listenerAttached) {
    confirmBtn.dataset.listenerAttached = 'true';
    confirmBtn.addEventListener('click', async () => {
      const noteId = confirmBtn.dataset.noteId;
      if (!noteId) return;

      try {
        const res = await fetch(`/api/notes/${noteId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Delete failed');

        // Hide modal
        const modal = document.getElementById('deleteModal');
        if (modal) bootstrap.Modal.getOrCreateInstance(modal).hide();

        // Animate card removal
        const card = document.getElementById(`card-${noteId}`);
        if (card) {
          card.classList.add('removing');
          card.addEventListener('animationend', () => {
            card.remove();
            // Update count
            const countEl = document.getElementById('total-notes');
            if (countEl) {
              const current = parseInt(countEl.textContent, 10) || 1;
              countEl.textContent = Math.max(0, current - 1);
            }
            // Show empty state if no cards left
            const grid = document.getElementById('notes-grid');
            if (grid && grid.querySelectorAll('.note-card').length === 0) {
              grid.innerHTML = `<div class="empty-state" id="empty-state">
                <span class="empty-emoji">📝</span>
                <h4>No notes yet</h4>
                <p>Create your first note to get started!</p>
                <a href="/note/new" class="btn btn-primary btn-new-note">
                  <i class="fa fa-plus"></i> Create a Note
                </a>
              </div>`;
            }
          }, { once: true });
        }
        showAlert('Note deleted.', 'success');
      } catch (err) {
        showAlert('Delete failed: ' + err.message, 'danger');
      }
    });
  }
}

/* ============================================================
   6. BACKUP (settings page)
   ============================================================ */
const BackupManager = (() => {
  function init() {
    // Export backup
    const exportBtn = document.getElementById('btn-backup-export');
    if (exportBtn) {
      exportBtn.addEventListener('click', async () => {
        try {
          exportBtn.disabled = true;
          exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Exporting…';
          const res = await fetch('/api/backup/export');
          if (!res.ok) throw new Error('Export failed');
          const blob = await res.blob();
          const date = new Date().toISOString().slice(0, 10);
          triggerDownload(blob, `smart-notepad-backup-${date}.json`);
          showAlert('Backup exported successfully!', 'success');
        } catch (err) {
          showAlert('Export failed: ' + err.message, 'danger');
        } finally {
          exportBtn.disabled = false;
          exportBtn.innerHTML = '<i class="fa fa-download"></i> Export Backup';
        }
      });
    }

    // Import backup
    const importInput = document.getElementById('backup-import-file');
    if (importInput) {
      importInput.addEventListener('change', async () => {
        const file = importInput.files[0];
        if (!file) return;

        const confirmImport = window.confirm(
          'Importing will REPLACE all existing notes. This cannot be undone. Continue?'
        );
        if (!confirmImport) { importInput.value = ''; return; }

        const btn = document.getElementById('btn-backup-import');
        if (btn) {
          btn.disabled = true;
          btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Importing…';
        }

        try {
          const formData = new FormData();
          formData.append('file', file);
          const res = await fetch('/api/backup/import', { method: 'POST', body: formData });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Import failed');
          showAlert(`Backup imported: ${data.imported || 0} note(s) restored.`, 'success');
        } catch (err) {
          showAlert('Import failed: ' + err.message, 'danger');
        } finally {
          importInput.value = '';
          if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa fa-upload"></i> Import Backup';
          }
        }
      });

      // The import button triggers the hidden file input
      const importBtn = document.getElementById('btn-backup-import');
      if (importBtn) {
        importBtn.addEventListener('click', () => importInput.click());
      }
    }
  }

  return { init };
})();

/* ============================================================
   7. SETTINGS — Theme buttons
   ============================================================ */
function initSettingsThemeButtons() {
  document.querySelectorAll('.theme-btn[data-theme-value]').forEach(btn => {
    btn.addEventListener('click', () => {
      ThemeManager.setTheme(btn.dataset.themeValue);
    });
  });
}

/* ============================================================
   8. FLASH MESSAGES — auto-dismiss after 4 seconds
   ============================================================ */
function initFlashMessages() {
  document.querySelectorAll('.alert.auto-dismiss, .alert[data-auto-dismiss]').forEach(alert => {
    setTimeout(() => {
      if (alert && alert.parentNode) {
        try {
          bootstrap.Alert.getOrCreateInstance(alert).close();
        } catch {
          alert.remove();
        }
      }
    }, 4000);
  });

  // Also dismiss any flash messages inside a .flash-messages wrapper
  document.querySelectorAll('.flash-messages .alert').forEach(alert => {
    setTimeout(() => {
      if (alert && alert.parentNode) {
        try {
          bootstrap.Alert.getOrCreateInstance(alert).close();
        } catch {
          alert.style.transition = 'opacity 0.4s';
          alert.style.opacity    = '0';
          setTimeout(() => alert.remove(), 400);
        }
      }
    }, 4000);
  });
}

/* ============================================================
   9. TOOLTIPS — Bootstrap tooltips
   ============================================================ */
function initTooltips() {
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach(el => {
    bootstrap.Tooltip.getOrCreateInstance(el);
  });
}

/* ============================================================
   DARK MODE TOGGLE BUTTON
   ============================================================ */
function initDarkModeToggle() {
  const btn = document.getElementById('darkModeToggle');
  if (btn) {
    btn.addEventListener('click', () => ThemeManager.toggle());
  }
}

/* ============================================================
   BODY THEME INIT (before DOM loads to avoid FOUC)
   ============================================================ */
(function () {
  const pref = localStorage.getItem('theme') || 'system';
  const effective = pref === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : pref;
  document.body.setAttribute('data-theme', effective);
})();

/* ============================================================
   DOM CONTENT LOADED — wire everything up
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  // Re-apply theme (icons need DOM)
  ThemeManager.init();

  // Dark mode toggle button
  initDarkModeToggle();

  // Flash messages
  initFlashMessages();

  // Tooltips
  initTooltips();

  // Dashboard notes loader
  NotesLoader.init();

  // Search
  SearchManager.init();

  // Editor
  NoteEditor.init();

  // Dashboard delete listeners (may also be called after dynamic render)
  attachDashboardDeleteListeners();

  // Backup manager (settings page)
  BackupManager.init();

  // Settings theme buttons
  initSettingsThemeButtons();

  // Page fade-in
  document.body.classList.add('page-enter');
});
