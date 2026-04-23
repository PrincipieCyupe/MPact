/* Mpact — Public site JS */
(function(){
  'use strict';

  /* Toast system */
  window.mpactToast = function(message, type) {
    type = type || 'info';
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>' +
      (type === 'success' ? '<path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>' :
       type === 'error' ? '<path d="M6 6l4 4M10 6l-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>' :
       '<path d="M8 5v3M8 10.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>') +
      '</svg>' + message;
    container.appendChild(el);
    setTimeout(function(){ el.classList.add('toast-out'); }, 3500);
    setTimeout(function(){ el.remove(); }, 3900);
  };

  /* Button loading state */
  window.btnLoading = function(btn, loading) {
    if (loading) {
      btn.classList.add('loading');
      btn.disabled = true;
      const span = btn.querySelector('.btn-text');
      if (span) span.style.opacity = '0';
    } else {
      btn.classList.remove('loading');
      btn.disabled = false;
      const span = btn.querySelector('.btn-text');
      if (span) span.style.opacity = '1';
    }
  };

  /* Apply form: project count hint */
  const projectsField = document.getElementById('projects');
  const projectHint = document.getElementById('project-count-hint');
  if (projectsField && projectHint) {
    projectsField.addEventListener('input', function() {
      const lines = this.value.split('\n').filter(l => l.trim()).length;
      projectHint.textContent = lines + ' project' + (lines !== 1 ? 's' : '') + ' detected';
    });
  }

  /* Apply form: submit with loading */
  const applyForm = document.getElementById('apply-form');
  if (applyForm) {
    applyForm.addEventListener('submit', function() {
      const btn = applyForm.querySelector('button[type="submit"]');
      if (btn) btnLoading(btn, true);
    });
  }

  /* Auto-dismiss flash messages */
  document.querySelectorAll('.flash').forEach(function(el) {
    setTimeout(function() { el.style.transition = 'opacity .3s'; el.style.opacity = '0'; setTimeout(function(){ el.remove(); }, 300); }, 5500);
  });

  /* Nav scroll shadow */
  var nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', function() {
      nav.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  /* Animate demo score bars on page load */
  requestAnimationFrame(function() {
    document.querySelectorAll('.demo-bar').forEach(function(bar) {
      var target = bar.style.width;
      bar.style.width = '0%';
      setTimeout(function() { bar.style.width = target; }, 400);
    });
  });

})();
