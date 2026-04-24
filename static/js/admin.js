/* Mpact — Admin Dashboard v2 */
(function () {
  'use strict';

  /* ── Toast ──────────────────────────────────────────────────── */
  function toast(message, type) {
    if (window.mpactToast) return window.mpactToast(message, type);
    type = type || 'info';
    let c = document.getElementById('toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-container';
      c.className = 'toast-container';
      document.body.appendChild(c);
    }
    const el = document.createElement('div');
    el.className = 'toast toast-' + type;
    el.innerHTML = (type === 'success' ? '✓ ' : type === 'error' ? '✕ ' : 'ℹ ') + message;
    c.appendChild(el);
    setTimeout(() => el.classList.add('toast-out'), 3800);
    setTimeout(() => el.remove(), 4200);
  }
  window.adminToast = toast;

  /* ── Button loading ──────────────────────────────────────────── */
  function btnLoad(btn, on) {
    if (on) { btn.classList.add('loading'); btn.disabled = true; }
    else     { btn.classList.remove('loading'); btn.disabled = false; }
  }

  /* ── Helpers ─────────────────────────────────────────────────── */
  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  }
  function scoreColor(v) { if (v == null) return 'muted'; return v >= 75 ? 'high' : v >= 50 ? 'mid' : 'low'; }
  function scoreBg(v)    { if (v == null) return 'var(--muted)'; return v >= 75 ? 'var(--success)' : v >= 50 ? 'var(--warn)' : 'var(--danger)'; }
  function locIcon()     { return '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>'; }

  /* ── Candidate Drawer ────────────────────────────────────────── */
  const overlay  = document.getElementById('drawer-overlay');
  const panel    = document.getElementById('drawer-panel');
  const drawerBody = document.getElementById('drawer-body');

  window.openDrawer = function (applicantId) {
    if (!overlay || !drawerBody) return;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    drawerBody.innerHTML = skeletonHTML();
    fetch('/recruiter/applicant/' + applicantId + '.json')
      .then(r => r.json())
      .then(data => { drawerBody.innerHTML = renderCandidate(data); })
      .catch(() => {
        drawerBody.innerHTML = '<p style="color:var(--danger);padding:24px">Failed to load candidate.</p>';
      });
  };

  window.closeDrawer = function () {
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  };

  if (overlay) {
    overlay.addEventListener('click', e => { if (e.target === overlay) window.closeDrawer(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') window.closeDrawer(); });
  }

  /* ── Skeleton ────────────────────────────────────────────────── */
  function skeletonHTML() {
    return `<div style="padding:4px">
      <div class="flex items-center gap-md mb-md">
        <div class="skeleton skeleton-circle" style="width:54px;height:54px"></div>
        <div class="flex-1">
          <div class="skeleton skeleton-heading"></div>
          <div class="skeleton skeleton-text" style="width:45%"></div>
        </div>
      </div>
      <hr class="divider">
      ${'<div class="skeleton skeleton-text"></div>'.repeat(4)}
      <div class="skeleton skeleton-text" style="width:60%"></div>
      <hr class="divider">
      <div class="skeleton skeleton-heading" style="width:35%"></div>
      ${'<div class="skeleton skeleton-text"></div>'.repeat(3)}
    </div>`;
  }

  /* ── Score Ring SVG ──────────────────────────────────────────── */
  function scoreRingSVG(value, size, color) {
    size = size || 64;
    const r = size / 2 - 7;
    const circ = 2 * Math.PI * r;
    const offset = (1 - (value || 0) / 100) * circ;
    return `<div class="score-ring" style="width:${size}px;height:${size}px">
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="var(--bg-inset)" stroke-width="7"/>
        <circle cx="${size/2}" cy="${size/2}" r="${r}" fill="none" stroke="${color}" stroke-width="7"
                stroke-dasharray="${circ.toFixed(1)}" stroke-dashoffset="${offset.toFixed(1)}"
                stroke-linecap="round" style="transition:stroke-dashoffset .8s cubic-bezier(.4,0,.2,1)"/>
      </svg>
      <div class="score-ring-label">
        <span class="score-ring-value" style="color:${color};font-size:1rem">${value != null ? Math.round(value) : '—'}</span>
        <span class="score-ring-sub">Score</span>
      </div>
    </div>`;
  }

  /* ── Score row ───────────────────────────────────────────────── */
  function scoreRow(label, val, accent) {
    const v  = val != null ? val.toFixed(1) : '—';
    const pct = val != null ? Math.min(val, 100) : 0;
    const bg  = accent ? 'var(--accent)' : scoreBg(val);
    return `<div style="margin-bottom:12px">
      <div class="flex justify-between items-center mb-xs">
        <span class="text-sm text-secondary">${label}</span>
        <span class="score-value ${accent ? '' : scoreColor(val)}" style="${accent ? 'color:var(--accent)' : ''}">${v}</span>
      </div>
      <div class="score-bar">
        <div class="score-bar-fill" style="width:${pct}%;background:${bg}"></div>
      </div>
    </div>`;
  }

  /* ── Skill level badge ──────────────────────────────────────── */
  function levelBadge(level) {
    const colors = {
      expert:       'background:#064e3b;color:#6ee7b7',
      advanced:     'background:#1e3a5f;color:#93c5fd',
      intermediate: 'background:#374151;color:#d1d5db',
      beginner:     'background:#3b2f14;color:#fbbf24',
    };
    const style = colors[(level || '').toLowerCase()] || colors.intermediate;
    return `<span style="font-size:.65rem;font-weight:700;padding:2px 7px;border-radius:99px;${style}">${esc(level || 'intermediate')}</span>`;
  }

  /* ── Full candidate render ───────────────────────────────────── */
  function renderCandidate(d) {
    const finalColor = scoreBg(d.scores.final);
    let html = '';

    // ── Header ──
    html += `<div class="flex items-start gap-md" style="margin-bottom:${d.headline ? '8px' : '16px'}">
      <div style="position:relative;flex-shrink:0">
        ${scoreRingSVG(d.scores.final, 72, finalColor)}
      </div>
      <div class="flex-1" style="min-width:0">
        <div class="flex items-center gap-sm flex-wrap" style="margin-bottom:4px">
          <h3 style="margin:0">${esc(d.name)}</h3>
          ${d.recommendation ? `<span class="badge badge-${d.recommendation_tone}">${esc(d.recommendation_label)}</span>` : ''}
          ${d.bias_flag ? `<span class="bias-flag" title="${esc(d.bias_notes || 'Flag for closer review')}">⚠ Review closely</span>` : ''}
        </div>
        ${d.headline ? `<div class="text-sm font-medium" style="color:var(--accent);margin-bottom:3px">${esc(d.headline)}</div>` : ''}
        <div class="text-sm text-secondary">${esc(d.email || '')}${d.phone ? ' · ' + esc(d.phone) : ''}</div>
        ${d.location ? `<div class="text-xs text-tertiary mt-xs">${locIcon()} ${esc(d.location)}</div>` : ''}
      </div>
    </div>`;

    // Availability + social links row
    const socialLinks = [];
    if (d.linkedin) socialLinks.push(`<a href="${esc(d.linkedin)}" target="_blank" rel="noopener" style="font-size:.75rem;color:var(--accent)">LinkedIn</a>`);
    if (d.github)   socialLinks.push(`<a href="${esc(d.github)}"   target="_blank" rel="noopener" style="font-size:.75rem;color:var(--accent)">GitHub</a>`);
    if (d.portfolio_url) socialLinks.push(`<a href="${esc(d.portfolio_url)}" target="_blank" rel="noopener" style="font-size:.75rem;color:var(--accent)">Portfolio</a>`);

    if (d.availability_status || socialLinks.length) {
      html += `<div class="flex gap-sm flex-wrap items-center" style="margin-bottom:14px;margin-top:6px">`;
      if (d.availability_status) {
        const avColors = { available:'var(--success)', open:'var(--accent)', 'not-available':'var(--text-tertiary)' };
        const avLabels = { available:'Available now', open:'Open to offers', 'not-available':'Not available' };
        const col = avColors[d.availability_status] || 'var(--text-tertiary)';
        html += `<span style="font-size:.72rem;padding:3px 8px;border-radius:99px;border:1px solid ${col};color:${col}">● ${avLabels[d.availability_status] || d.availability_status}</span>`;
      }
      if (d.availability_type) {
        html += `<span class="badge badge-muted" style="font-size:.68rem">${esc(d.availability_type)}</span>`;
      }
      socialLinks.forEach(l => { html += l; });
      html += '</div>';
    }

    // Bio
    if (d.bio) {
      html += `<div style="font-size:.85rem;color:var(--text-secondary);line-height:1.65;background:var(--bg-inset);border-radius:var(--r-sm);padding:10px 14px;margin-bottom:14px">${esc(d.bio)}</div>`;
    }

    // Bias notes banner
    if (d.bias_flag && d.bias_notes) {
      html += `<div style="background:var(--warn-bg);border:1px solid #FDE68A;border-radius:var(--r);padding:10px 14px;margin-bottom:16px">
        <div class="text-xs font-semibold" style="color:var(--warn);margin-bottom:3px">⚠ Flag for review</div>
        <div class="text-xs text-secondary">${esc(d.bias_notes)}</div>
      </div>`;
    }

    html += '<hr class="divider">';

    // ── Scores ──
    html += '<h4 style="margin-bottom:14px">Score Breakdown</h4>';
    html += scoreRow('Skills Match', d.scores.skills);
    html += scoreRow('Experience', d.scores.experience);
    html += scoreRow('Education', d.scores.education);
    html += scoreRow('Projects', d.scores.projects);
    html += `<div style="border-top:1px solid var(--border-light);margin:10px 0 12px"></div>`;
    html += scoreRow('Criteria match', d.scores.weighted);
    html += scoreRow('Qualitative fit (AI)', d.scores.ai, true);

    if (d.scores.ai != null && d.scores.weighted != null) {
      const delta = +(d.scores.ai - d.scores.weighted).toFixed(1);
      const sign = delta >= 0 ? '+' : '';
      const deltaColor = delta > 2 ? 'var(--success)' : (delta < -2 ? 'var(--warn)' : 'var(--text-tertiary)');
      const deltaBg = delta > 2 ? 'var(--success-bg)' : (delta < -2 ? 'var(--warn-bg)' : 'var(--bg-inset)');
      html += `<div style="display:flex;align-items:center;justify-content:space-between;background:${deltaBg};border-radius:var(--r-sm);padding:8px 12px;margin-top:8px">
        <span class="text-xs" style="color:var(--text-secondary)">AI adjustment vs deterministic</span>
        <span style="font-weight:700;font-size:.82rem;color:${deltaColor};font-family:var(--font-mono)">${sign}${delta}</span>
      </div>`;
    }

    html += `<div style="background:var(--bg-inset);border-radius:var(--r-sm);padding:8px 12px;margin-top:8px;display:flex;align-items:center;justify-content:space-between">
      <span class="text-xs text-tertiary">Final Score (60/40 blend)</span>
      <span style="font-weight:800;font-size:1rem;font-family:var(--font-mono);color:${scoreBg(d.scores.final)}">${d.scores.final != null ? d.scores.final.toFixed(1) : '—'}</span>
    </div>`;

    html += '<hr class="divider">';

    // ── Skills (structured) ──
    html += '<h4 style="margin-bottom:12px">Profile</h4>';
    if (d.structured_skills && d.structured_skills.length) {
      html += `<div style="margin-bottom:14px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Skills</div>
        <div style="display:flex;flex-direction:column;gap:5px">
          ${d.structured_skills.map(s => `
            <div style="display:flex;align-items:center;gap:7px">
              ${levelBadge(s.level)}
              <span class="text-sm">${esc(s.name)}</span>
              ${s.yearsOfExperience ? `<span class="text-xs text-tertiary">${s.yearsOfExperience}yr</span>` : ''}
            </div>`).join('')}
        </div>
      </div>`;
    } else if (d.skills && d.skills.length) {
      html += `<div style="margin-bottom:12px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Skills</div>
        <div style="display:flex;flex-wrap:wrap;gap:5px">
          ${d.skills.map(s => `<span class="tag">${esc(s)}</span>`).join('')}
        </div>
      </div>`;
    }

    // Languages
    if (d.languages && d.languages.length) {
      html += `<div style="margin-bottom:14px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Languages</div>
        <div style="display:flex;flex-wrap:wrap;gap:6px">
          ${d.languages.map(l => `<span class="tag">${esc(l.name || l.language || '')} <span class="text-tertiary" style="font-size:.68rem">${esc(l.proficiency || '')}</span></span>`).join('')}
        </div>
      </div>`;
    }

    // Core profile items
    const profileItems = [
      ['Experience', (d.years_experience || 0) + ' years'],
      ['Education',  d.education ? esc(d.education) + (d.education_level ? ` <span class="badge badge-muted" style="font-size:.68rem">${d.education_level}</span>` : '') : null],
      ['Projects',   d.project_count ? d.project_count + ' project(s)' : null],
    ];
    profileItems.forEach(([label, val]) => {
      if (!val) return;
      html += `<div class="flex gap-sm items-start" style="margin-bottom:8px;font-size:.875rem">
        <span style="width:84px;font-weight:500;color:var(--text-tertiary);flex-shrink:0;padding-top:1px">${label}</span>
        <span>${val}</span>
      </div>`;
    });

    // Structured education
    if (d.structured_education && d.structured_education.length) {
      html += `<div style="margin-top:10px;margin-bottom:14px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Education</div>
        ${d.structured_education.map(e => `
          <div style="padding:8px 10px;background:var(--bg-inset);border-radius:var(--r-sm);margin-bottom:6px">
            <div class="text-sm font-semibold">${esc(e.degree || '')} ${e.field ? '· ' + esc(e.field) : ''}</div>
            <div class="text-xs text-tertiary">${esc(e.institution || '')}${(e.startYear || e.endYear) ? ' · ' + (e.startYear || '') + (e.endYear ? '–' + e.endYear : '') : ''}</div>
          </div>`).join('')}
      </div>`;
    }

    // Certifications
    if (d.certifications && d.certifications.length) {
      html += `<div style="margin-bottom:14px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Certifications</div>
        ${d.certifications.map(c => `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>
            <span class="text-sm">${esc(c.name)}</span>
            ${c.issuer ? `<span class="text-xs text-tertiary">· ${esc(c.issuer)}</span>` : ''}
            ${c.date ? `<span class="text-xs text-tertiary">${esc(c.date)}</span>` : ''}
          </div>`).join('')}
      </div>`;
    }

    // Experience timeline
    if (d.structured_experience && d.structured_experience.length) {
      html += '<hr class="divider">';
      html += '<h4 style="margin-bottom:12px">Experience</h4>';
      d.structured_experience.forEach(exp => {
        const period = [exp.startDate, exp.isCurrent ? 'Present' : exp.endDate].filter(Boolean).join(' – ');
        html += `<div style="padding:10px 12px;border-left:3px solid var(--border-light);margin-bottom:12px">
          <div class="text-sm font-semibold">${esc(exp.role || exp.title || '')}</div>
          <div class="text-xs" style="color:var(--accent)">${esc(exp.company || '')}${period ? ' · ' + period : ''}</div>
          ${exp.description ? `<div class="text-xs text-secondary" style="margin-top:5px;line-height:1.6">${esc(exp.description)}</div>` : ''}
        </div>`;
      });
    }

    // Structured projects
    if (d.structured_projects && d.structured_projects.length) {
      html += `<div style="margin-top:${d.structured_experience && d.structured_experience.length ? '0' : '10px'};margin-bottom:14px">
        <div class="text-xs font-semibold text-tertiary mb-xs" style="text-transform:uppercase;letter-spacing:.05em">Projects</div>
        ${d.structured_projects.map(p => `
          <div style="padding:8px 10px;background:var(--bg-inset);border-radius:var(--r-sm);margin-bottom:6px">
            <div class="text-sm font-semibold">${p.url ? `<a href="${esc(p.url)}" target="_blank" style="color:var(--accent)">${esc(p.name)}</a>` : esc(p.name)}</div>
            ${p.description ? `<div class="text-xs text-secondary" style="margin-top:3px;line-height:1.55">${esc(p.description)}</div>` : ''}
          </div>`).join('')}
      </div>`;
    } else if (d.projects) {
      html += `<div style="margin-top:8px;background:var(--bg-inset);border-radius:var(--r-sm);padding:10px 12px;font-size:.82rem;color:var(--text-secondary);white-space:pre-line;line-height:1.6">${esc(d.projects)}</div>`;
    }

    // Resume download
    if (d.has_resume) {
      html += `<a href="/recruiter/applicant/${d.id}/resume" class="btn btn-secondary btn-sm mt-sm" style="display:inline-flex">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Download Resume PDF
      </a>`;
    }

    // ── Evaluation ──
    if (d.strengths.length || d.gaps.length || d.reasoning) {
      html += '<hr class="divider">';
      html += '<h4 style="margin-bottom:12px">AI Evaluation</h4>';

      if (d.strengths.length) {
        html += `<div style="margin-bottom:14px">
          <div class="text-xs font-semibold mb-xs" style="color:var(--success);text-transform:uppercase;letter-spacing:.05em">✓ Strengths</div>
          ${d.strengths.map(s => `<div class="flex items-start gap-xs mb-xs text-sm" style="color:var(--text-secondary)">
            <span style="color:var(--success);flex-shrink:0;margin-top:2px;font-weight:700">·</span>
            <span>${esc(s)}</span>
          </div>`).join('')}
        </div>`;
      }

      if (d.gaps.length) {
        html += `<div style="margin-bottom:14px">
          <div class="text-xs font-semibold mb-xs" style="color:var(--warn);text-transform:uppercase;letter-spacing:.05em">△ Areas to address</div>
          ${d.gaps.map(g => `<div class="flex items-start gap-xs mb-xs text-sm" style="color:var(--text-secondary)">
            <span style="color:var(--warn);flex-shrink:0;margin-top:2px;font-weight:700">·</span>
            <span>${esc(g)}</span>
          </div>`).join('')}
        </div>`;
      }

      if (d.reasoning) {
        html += `<div style="background:var(--bg-inset);border-radius:var(--r);padding:14px 16px;border-left:3px solid var(--accent)">
          <div class="text-xs font-semibold mb-xs" style="color:var(--accent);text-transform:uppercase;letter-spacing:.05em">Reviewer notes</div>
          <div class="text-sm" style="color:var(--text-secondary);font-style:italic;line-height:1.65">${esc(d.reasoning)}</div>
        </div>`;
      }
    }

    // ── Custom Q&A ──
    if (d.custom_qa && d.custom_qa.length) {
      html += '<hr class="divider">';
      html += '<h4 style="margin-bottom:12px">Application Responses</h4>';
      d.custom_qa.forEach(qa => {
        html += `<div style="margin-bottom:14px">
          <div class="text-xs font-semibold text-tertiary" style="text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px">${esc(qa.label)}</div>
          <div class="text-sm" style="color:var(--text-secondary);background:var(--bg-inset);border-radius:var(--r-sm);padding:10px 12px;line-height:1.6">${esc(qa.answer)}</div>
        </div>`;
      });
    }

    // ── Recruiter notes ──
    html += '<hr class="divider">';
    html += '<h4 style="margin-bottom:10px">Recruiter Notes</h4>';
    html += `<textarea id="recruiter-notes-${d.id}" rows="3"
      style="width:100%;box-sizing:border-box;padding:10px 12px;font-size:13px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--bg-inset);color:var(--text-primary);resize:vertical;line-height:1.5;font-family:inherit"
      placeholder="Add private notes about this candidate…">${esc(d.recruiter_notes || '')}</textarea>`;
    html += `<button class="btn btn-secondary btn-sm" style="margin-top:8px"
      onclick="saveNotes(${d.id})">Save Notes</button>`;

    // ── Status ──
    html += '<hr class="divider">';
    html += '<h4 style="margin-bottom:12px">Recruiter Action</h4>';
    html += '<div class="flex gap-sm flex-wrap">';
    const statuses = [
      { key: 'shortlisted', label: '✓ Shortlist',        style: 'btn-success' },
      { key: 'interview',   label: '📅 Interview',        style: 'btn-primary' },
      { key: 'reviewed',    label: 'Mark Reviewed',       style: 'btn-secondary' },
      { key: 'rejected',    label: '✕ Reject',            style: 'btn-ghost', extra: 'color:var(--danger)' },
    ];
    statuses.forEach(s => {
      const active = d.status === s.key;
      html += `<button class="btn ${active ? 'btn-primary' : s.style} btn-sm"
        style="${s.extra || ''}"
        onclick="updateStatus(${d.id}, '${s.key}', this)">${s.label}</button>`;
    });
    html += '</div>';

    return html;
  }

  /* ── Update status ───────────────────────────────────────────── */
  window.updateStatus = function (applicantId, status, btn) {
    btnLoad(btn, true);
    fetch('/recruiter/applicant/' + applicantId + '/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }).then(r => r.json()).then(data => {
      btnLoad(btn, false);
      if (data.ok) {
        toast('Status updated to ' + status, 'success');
        window.openDrawer(applicantId);
        const row = document.querySelector('[data-applicant-id="' + applicantId + '"]');
        if (row) {
          const badge = row.querySelector('.status-badge');
          if (badge) {
            badge.className = 'badge status-badge badge-' + statusTone(status);
            badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
          }
        }
      } else { toast(data.error || 'Failed', 'error'); }
    }).catch(() => { btnLoad(btn, false); toast('Network error', 'error'); });
  };

  function statusTone(s) {
    return { shortlisted: 'success', interview: 'accent', reviewed: 'info', rejected: 'danger', new: 'muted' }[s] || 'muted';
  }

  /* ── Save recruiter notes ────────────────────────────────────── */
  window.saveNotes = function (applicantId) {
    const ta = document.getElementById('recruiter-notes-' + applicantId);
    if (!ta) return;
    fetch('/recruiter/applicant/' + applicantId + '/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: ta.value }),
    }).then(r => r.json()).then(data => {
      if (data.ok) toast('Notes saved', 'success');
      else toast('Failed to save notes', 'error');
    }).catch(() => toast('Network error', 'error'));
  };

  /* ── Weight Sliders ──────────────────────────────────────────── */
  const sliders = document.querySelectorAll('.weight-slider');
  const totalDisplay = document.getElementById('weight-total');
  function updateWeightTotal() {
    if (!totalDisplay) return;
    let sum = 0;
    sliders.forEach(s => { sum += parseInt(s.value) || 0; });
    totalDisplay.textContent = sum;
    totalDisplay.className = 'weight-total ' + (sum === 100 ? 'valid' : 'invalid');
  }
  sliders.forEach(s => {
    const valSpan = document.getElementById(s.dataset.display);
    s.addEventListener('input', () => {
      if (valSpan) valSpan.textContent = s.value;
      updateWeightTotal();
    });
  });
  updateWeightTotal();

  /* ── Auto-dismiss flash messages ────────────────────────────── */
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .3s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 320);
    }, 5500);
  });

  /* ── Nav scroll shadow ───────────────────────────────────────── */
  const nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  /* ── Animate score bars on page load ────────────────────────── */
  requestAnimationFrame(() => {
    document.querySelectorAll('.rank-score-bar-fill, .score-bar-fill').forEach(bar => {
      if (bar.classList.contains('demo-bar')) return;
      const target = bar.style.width;
      bar.style.width = '0%';
      setTimeout(() => { bar.style.width = target; }, 100 + Math.random() * 150);
    });
  });

})();
