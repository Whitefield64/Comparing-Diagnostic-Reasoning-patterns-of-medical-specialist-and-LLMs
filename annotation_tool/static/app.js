'use strict';

// ── Label definitions ─────────────────────────────────────────
const LABELS = {
  1:  { name: 'ABD_SELECTIVE',   color: '#FF4D4D', lightText: false },
  2:  { name: 'ABD_CREATIVE',    color: '#FF7043', lightText: false },
  3:  { name: 'ABD_VISUAL',      color: '#FF9800', lightText: true  },
  4:  { name: 'ABD_CAUSAL',      color: '#FFC107', lightText: true  },
  5:  { name: 'DED_HYPOTHETICO', color: '#AB47BC', lightText: false },
  6:  { name: 'DED_ALGORITHMIC', color: '#7E57C2', lightText: false },
  7:  { name: 'DED_HIERARCHICAL',color: '#5C6BC0', lightText: false },
  8:  { name: 'DED_VALIDATION',  color: '#3F51B5', lightText: false },
  9:  { name: 'IND_PATTERN',     color: '#66BB6A', lightText: false },
  10: { name: 'IND_INTUITION',   color: '#26A69A', lightText: false },
  11: { name: 'IND_BAYESIAN',    color: '#29B6F6', lightText: true  },
  12: { name: 'IND_CASEBASED',   color: '#42A5F5', lightText: false },
};

// ── localStorage keys ─────────────────────────────────────────
const LS_LAST_CASE      = 'ann_last_case';
const LS_LAST_ANNOTATOR = 'ann_last_annotator';
const lsContentKey  = (fname) => `ann_content_${fname}`;
const lsAnnsKey     = (fname, ann) => `ann_annotations_${fname}_${ann}`;

// ── State ─────────────────────────────────────────────────────
let rawText           = '';
let activeLabel       = null;
let annotations       = [];
let compareAnnotations= [];
let currentCase       = '';
let annotatorName     = '';
let pocRange          = null;
let popupAnnId        = null;
let mergeSelection    = [];   // up to 2 annotation IDs queued for merge

// ── DOM refs ──────────────────────────────────────────────────
const annotatorInput  = document.getElementById('annotator-input');
const caseNameDisplay = document.getElementById('case-name-display');
const doc             = document.getElementById('doc');
const docPlaceholder  = document.getElementById('doc-placeholder');
const annList         = document.getElementById('annotation-list');
const statsBar        = document.getElementById('stats-bar');
const jsonPreview     = document.getElementById('json-preview');
const warningBar      = document.getElementById('warning-bar');
const spanPopup       = document.getElementById('span-popup');
const popupLabelName  = document.getElementById('popup-label-name');
const popupDelete     = document.getElementById('popup-delete');
const btnClearCmp     = document.getElementById('btn-clear-compare');

// ── Boot: restore last session ────────────────────────────────
(function restoreSession() {
  const lastCase = localStorage.getItem(LS_LAST_CASE);
  const lastAnnotator = localStorage.getItem(LS_LAST_ANNOTATOR);
  if (!lastCase || !lastAnnotator) return;

  const content = localStorage.getItem(lsContentKey(lastCase));
  if (!content) return;

  annotatorName = lastAnnotator;
  annotatorInput.value = lastAnnotator;
  openCase(lastCase, content, /* silent */ true);
})();

// ── Load case file from PC ────────────────────────────────────
document.getElementById('load-case-file').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const raw = await file.text();
    // Normalise line endings so char offsets are consistent
    const text = raw.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    localStorage.setItem(lsContentKey(file.name), text);
    openCase(file.name, text, false);
  } catch (err) {
    alert('Could not read file: ' + err.message);
  }
  e.target.value = '';
});

function migrateLegacyAnnotation(a) {
  // Convert old merged format {ranges, text, merged:true} → {parts, merged:true}
  if (a.merged && a.ranges && !a.parts) {
    const texts = a.text ? a.text.split('...') : [];
    return {
      ...a,
      parts: a.ranges.map(([start, end], i) => ({ start, end, text: texts[i] ?? '' })),
      ranges: undefined,
      text: undefined,
    };
  }
  return a;
}

function openCase(fname, content, silent) {
  currentCase = fname;
  rawText = content;
  pocRange = detectPocRange(rawText);
  caseNameDisplay.textContent = fname;
  localStorage.setItem(LS_LAST_CASE, fname);

  const savedAnns = localStorage.getItem(lsAnnsKey(fname, annotatorName));
  if (savedAnns) {
    const parsed = JSON.parse(savedAnns).map(migrateLegacyAnnotation);
    if (parsed.length > 0 && !silent) {
      annotations = confirm(`Resume previous session? (${parsed.length} annotation(s) found)`)
        ? parsed : [];
    } else {
      annotations = parsed;
    }
  } else {
    annotations = [];
  }

  compareAnnotations = [];
  btnClearCmp.style.display = 'none';
  docPlaceholder.style.display = 'none';
  doc.style.display = 'block';
  render();
}

// ── Annotator input ───────────────────────────────────────────
annotatorInput.addEventListener('input', () => {
  annotatorName = annotatorInput.value.trim();
  localStorage.setItem(LS_LAST_ANNOTATOR, annotatorName);
  if (currentCase && annotatorName) {
    // Reload annotations for this annotator
    const saved = localStorage.getItem(lsAnnsKey(currentCase, annotatorName));
    annotations = saved ? JSON.parse(saved) : [];
    render();
  }
});

// ── Palette wiring ────────────────────────────────────────────
document.querySelectorAll('.label-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const n = parseInt(btn.dataset.label);
    if (activeLabel === n) {
      activeLabel = null;
      document.querySelectorAll('.label-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('active-label-display').textContent = 'No label selected';
    } else {
      activeLabel = n;
      document.querySelectorAll('.label-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('active-label-display').textContent =
        `Active: ${n} \u00b7 ${LABELS[n].name}`;
    }
  });
});

// ── PoC range detection ───────────────────────────────────────
function detectPocRange(text) {
  const pocRe    = /^##\s+Presentation of Case/im;
  const nextSecRe= /^##\s+/gm;
  const pocMatch = pocRe.exec(text);
  if (!pocMatch) return null;
  const start = pocMatch.index;
  nextSecRe.lastIndex = start + pocMatch[0].length;
  const nextMatch = nextSecRe.exec(text);
  return { start, end: nextMatch ? nextMatch.index : text.length };
}

// ── Render document ───────────────────────────────────────────
function render() {
  const allAnns = [
    ...annotations.map(a => ({ ...a, isCompare: false })),
    ...compareAnnotations.map(a => ({ ...a, isCompare: true })),
  ];

  const events = [];
  allAnns.forEach(a => {
    getRanges(a).forEach(([s, e]) => {
      events.push({ pos: s, type: 'open',  ann: a });
      events.push({ pos: e, type: 'close', ann: a });
    });
  });
  events.sort((a, b) => a.pos - b.pos || (a.type === 'close' ? -1 : 1));

  let html = '';
  let i    = 0;
  let eIdx = 0;
  const open = new Set();

  while (i < rawText.length || eIdx < events.length) {
    while (eIdx < events.length && events[eIdx].pos <= i) {
      const ev = events[eIdx++];
      if (ev.type === 'close') {
        if (open.has(ev.ann.id)) { open.delete(ev.ann.id); html += '</span>'; }
      } else {
        open.add(ev.ann.id);
        const cls = ev.ann.isCompare ? 'hl compare' : 'hl';
        html += `<span class="${cls}" data-id="${ev.ann.id}" data-label="${ev.ann.label}">`;
      }
    }
    if (i >= rawText.length) break;
    const nextEvent = eIdx < events.length ? events[eIdx].pos : rawText.length;
    html += encodeChunk(rawText.slice(i, nextEvent), i);
    i = nextEvent;
  }
  open.forEach(() => { html += '</span>'; });

  doc.innerHTML = html;
  wrapPocZone();
  attachHighlightListeners();
  renderPanel();
}

function encodeChunk(chunk, startPos) {
  const parts = chunk.split('\n');
  let out = '';
  parts.forEach((line, idx) => {
    if (line.startsWith('### ')) {
      out += `<span class="md-h3"><span class="md-pfx" aria-hidden="true">### </span>${escHtml(line.slice(4))}</span>`;
    } else if (line.startsWith('## ')) {
      out += `<span class="md-h2"><span class="md-pfx" aria-hidden="true">## </span>${escHtml(line.slice(3))}</span>`;
    } else if (line.startsWith('# ')) {
      out += `<span class="md-h1"><span class="md-pfx" aria-hidden="true"># </span>${escHtml(line.slice(2))}</span>`;
    } else {
      out += escHtml(line);
    }
    if (idx < parts.length - 1) out += '\n';
  });
  return out;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function wrapPocZone() {
  if (!pocRange) return;
  const spans = Array.from(doc.querySelectorAll('.md-h2, .md-h3'));
  let pocStart = null, pocEnd = null;
  for (let i = 0; i < spans.length; i++) {
    if (spans[i].textContent.match(/Presentation of Case/i)) {
      pocStart = spans[i];
      pocEnd   = spans[i + 1] || null;
      break;
    }
  }
  if (!pocStart) return;
  const wrapDiv = document.createElement('div');
  wrapDiv.className = 'poc-zone';
  const parent = pocStart.parentNode;
  let node = pocStart;
  const nodesToMove = [];
  while (node && node !== pocEnd) { nodesToMove.push(node); node = node.nextSibling; }
  parent.insertBefore(wrapDiv, pocStart);
  nodesToMove.forEach(n => wrapDiv.appendChild(n));
}

// ── Char offset computation ───────────────────────────────────
// Uses Range.toString() so the measurement matches the browser's selection
// model exactly — including user-select:none regions that the TreeWalker
// would count but the browser skips when reporting selection boundaries.
function getAbsoluteOffset(node, nodeOffset) {
  try {
    const range = document.createRange();
    range.setStart(doc, 0);
    range.setEnd(node, nodeOffset);
    return range.toString().length;
  } catch (_) {
    return 0;
  }
}

// ── Mouse selection → annotation ─────────────────────────────
doc.addEventListener('mouseup', () => {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed) return;

  if (!activeLabel) {
    showWarning('Select a label from the palette first.');
    sel.removeAllRanges(); return;
  }
  if (!annotatorName) {
    showWarning('Enter your annotator name first.');
    sel.removeAllRanges(); return;
  }

  const range = sel.getRangeAt(0);
  const start = getAbsoluteOffset(range.startContainer, range.startOffset);
  const end   = getAbsoluteOffset(range.endContainer,   range.endOffset);
  if (start >= end) { sel.removeAllRanges(); return; }

  if (pocRange && start < pocRange.end && end > pocRange.start) {
    showWarning('\u26a0 The Presentation of Case section cannot be annotated.');
    sel.removeAllRanges(); return;
  }

  const overlap = annotations.find(a => getRanges(a).some(([rs, re]) => start < re && end > rs));
  if (overlap) {
    showWarning('\u26a0 This selection overlaps an existing annotation \u2014 delete it first.');
    sel.removeAllRanges(); return;
  }

  hideWarning();
  const text = rawText.slice(start, end);
  const id   = 'a' + Date.now() + Math.random().toString(36).slice(2, 6);
  annotations.push({ id, start, end, label: activeLabel,
                     label_name: LABELS[activeLabel].name, text, annotator: annotatorName });
  sel.removeAllRanges();
  autosave();
  render();
});

// ── Highlight click → popup ───────────────────────────────────
function attachHighlightListeners() {
  document.querySelectorAll('.hl:not(.compare)').forEach(el => {
    el.addEventListener('click', e => {
      e.stopPropagation();
      const id  = el.dataset.id;
      popupAnnId = id;
      const ann = annotations.find(a => a.id === id);
      if (!ann) return;
      popupLabelName.textContent = `${ann.label} \u00b7 ${ann.label_name}`;
      spanPopup.style.display = 'flex';
      const rect = el.getBoundingClientRect();
      spanPopup.style.left = `${rect.left}px`;
      spanPopup.style.top  = `${rect.top - 40}px`;
    });
  });
}

document.addEventListener('click', e => {
  if (!spanPopup.contains(e.target)) { spanPopup.style.display = 'none'; popupAnnId = null; }
});

popupDelete.addEventListener('click', () => {
  if (popupAnnId) removeAnnotation(popupAnnId);
  spanPopup.style.display = 'none';
  popupAnnId = null;
});

function removeAnnotation(id) {
  annotations = annotations.filter(a => a.id !== id);
  mergeSelection = mergeSelection.filter(x => x !== id);
  autosave();
  render();
}

function getRanges(ann) {
  if (ann.parts)  return ann.parts.map(p => [p.start, p.end]);
  if (ann.ranges) return ann.ranges;
  return [[ann.start, ann.end]];
}

function getFirstStart(ann) {
  if (ann.parts)  return ann.parts[0].start;
  if (ann.ranges) return ann.ranges[0][0];
  return ann.start;
}

function mergeAnnotations(...ids) {
  const anns = ids.map(id => annotations.find(x => x.id === id)).filter(Boolean);
  if (anns.length < 2) return;

  const firstLabel = anns[0].label;
  const mismatch = anns.find(a => a.label !== firstLabel);
  if (mismatch) {
    showWarning(`\u26a0 Cannot merge: labels differ (${anns[0].label_name} vs ${mismatch.label_name})`);
    mergeSelection = [];
    renderPanel();
    return;
  }

  // Flatten parts from all selected in positional order (handles already-merged)
  const allParts = anns
    .flatMap(a => a.parts ? a.parts : [{ start: a.start, end: a.end, text: a.text }])
    .sort((a, b) => a.start - b.start);

  const id = 'a' + Date.now() + Math.random().toString(36).slice(2, 6);
  annotations = annotations.filter(x => !ids.includes(x.id));
  annotations.push({
    id,
    parts: allParts,
    label: firstLabel,
    label_name: anns[0].label_name,
    annotator: annotatorName,
    merged: true,
  });
  mergeSelection = [];
  autosave();
  render();
}

function removePart(annId, partIdx) {
  const ann = annotations.find(x => x.id === annId);
  if (!ann || !ann.parts) return;
  const remaining = ann.parts.filter((_, i) => i !== partIdx);
  if (remaining.length === 0) {
    annotations = annotations.filter(x => x.id !== annId);
  } else if (remaining.length === 1) {
    const p = remaining[0];
    annotations = annotations.map(x => x.id !== annId ? x : {
      id: x.id, start: p.start, end: p.end,
      label: x.label, label_name: x.label_name, text: p.text, annotator: x.annotator,
    });
  } else {
    annotations = annotations.map(x => x.id !== annId ? x : { ...x, parts: remaining });
  }
  autosave();
  render();
}

// ── Right panel ───────────────────────────────────────────────
function renderPanel() {
  const cmpCount = compareAnnotations.length;
  if (cmpCount > 0) {
    const other = compareAnnotations[0]?.annotator || 'other';
    statsBar.textContent = `You: ${annotations.length} span(s)  \u00b7  ${other}: ${cmpCount} span(s)`;
  } else {
    statsBar.textContent = `${annotations.length} annotation(s)`;
  }

  const allCards = [
    ...annotations.map(a => ({ ...a, isCompare: false })),
    ...compareAnnotations.map(a => ({ ...a, isCompare: true })),
  ].sort((a, b) => getFirstStart(a) - getFirstStart(b));

  // Merge commit bar
  const existingMergeBar = document.getElementById('merge-commit-bar');
  if (existingMergeBar) existingMergeBar.remove();
  if (mergeSelection.length >= 2) {
    const bar = document.createElement('div');
    bar.id = 'merge-commit-bar';
    const btn = document.createElement('button');
    btn.className = 'merge-commit-btn';
    btn.textContent = `Merge ${mergeSelection.length} selected spans`;
    btn.addEventListener('click', () => mergeAnnotations(...mergeSelection));
    bar.appendChild(btn);
    annList.parentNode.insertBefore(bar, annList);
  }

  annList.innerHTML = '';
  allCards.forEach(ann => {
    const lbl  = LABELS[ann.label];
    const card = document.createElement('div');
    card.className = 'ann-card' + (mergeSelection.includes(ann.id) ? ' merge-selected' : '');
    card.style.borderLeftColor = lbl.color;

    const header = document.createElement('div');
    header.className = 'ann-card-header';

    const badge = document.createElement('span');
    badge.className = 'ann-badge' + (lbl.lightText ? ' light-text' : '');
    badge.style.background = lbl.color;
    badge.textContent = `${ann.label} \u00b7 ${lbl.name}`;
    header.appendChild(badge);

    if (!ann.isCompare) {
      const mergeBtn = document.createElement('button');
      mergeBtn.className = 'ann-merge-btn' + (mergeSelection.includes(ann.id) ? ' selected' : '');
      mergeBtn.textContent = '\u229e';
      mergeBtn.title = 'Select for merge';
      mergeBtn.addEventListener('click', () => {
        if (mergeSelection.includes(ann.id)) {
          mergeSelection = mergeSelection.filter(x => x !== ann.id);
        } else {
          mergeSelection.push(ann.id);
        }
        renderPanel();
      });
      header.appendChild(mergeBtn);
      const del = document.createElement('button');
      del.className = 'ann-delete-btn';
      del.textContent = '\u2715';
      del.title = 'Delete annotation';
      del.addEventListener('click', () => removeAnnotation(ann.id));
      header.appendChild(del);
    } else {
      const tag = document.createElement('span');
      tag.className = 'ann-compare-tag';
      tag.textContent = `(${ann.annotator})`;
      header.appendChild(tag);
    }
    card.appendChild(header);

    if (ann.parts) {
      const partsList = document.createElement('div');
      partsList.className = 'ann-parts-list';
      ann.parts.forEach((part, idx) => {
        const row = document.createElement('div');
        row.className = 'ann-part-row';

        const txt = document.createElement('span');
        txt.className = 'ann-part-text';
        txt.textContent = '\u201c' + part.text.replace(/\n/g,' ').slice(0, 55) + (part.text.length > 55 ? '\u2026' : '') + '\u201d';

        const rng = document.createElement('span');
        rng.className = 'ann-part-range';
        rng.textContent = `${part.start}\u2013${part.end}`;

        if (!ann.isCompare) {
          const pdel = document.createElement('button');
          pdel.className = 'ann-part-delete-btn';
          pdel.textContent = '\u2715';
          pdel.title = 'Remove this part';
          pdel.addEventListener('click', () => removePart(ann.id, idx));
          row.appendChild(txt); row.appendChild(rng); row.appendChild(pdel);
        } else {
          row.appendChild(txt); row.appendChild(rng);
        }
        partsList.appendChild(row);
      });
      card.appendChild(partsList);
    } else {
      const excerpt = document.createElement('div');
      excerpt.className = 'ann-excerpt';
      const displayText = ann.text || '';
      excerpt.textContent = '\u201c' + displayText.replace(/\n/g,' ').slice(0, 90) + (displayText.length > 90 ? '\u2026' : '') + '\u201d';
      card.appendChild(excerpt);

      const rangeEl = document.createElement('div');
      rangeEl.className = 'ann-range';
      rangeEl.textContent = 'chars ' + getRanges(ann).map(([s, e]) => `${s}\u2013${e}`).join(' \u00b7 ');
      card.appendChild(rangeEl);
    }

    annList.appendChild(card);
  });

  jsonPreview.textContent = JSON.stringify(buildExportPayload().annotations, null, 2);
}

// ── Export ────────────────────────────────────────────────────
document.getElementById('btn-export').addEventListener('click', exportJSON);

function buildExportPayload() {
  return {
    case: currentCase,
    annotator: annotatorName,
    exported_at: new Date().toISOString(),
    annotations: annotations.map(a => ({
      ranges: getRanges(a),
      label: a.label,
      label_name: a.label_name,
      text: a.parts ? a.parts.map(p => p.text).join('...') : a.text,
    })),
  };
}

function exportJSON() {
  if (!currentCase) { alert('Load a case first.'); return; }
  const blob = new Blob([JSON.stringify(buildExportPayload(), null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `${currentCase.replace(/\.md$/, '').replace(/\s+/g,'_')}_${annotatorName || 'anon'}.json`;
  a.click();
}

// ── Import (comparison) ───────────────────────────────────────
document.getElementById('import-file').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    compareAnnotations = (data.annotations || []).map(a => ({
      ...a, annotator: data.annotator || 'other', isCompare: true,
    }));
    btnClearCmp.style.display = 'inline-block';
    render();
  } catch (err) {
    alert('Could not parse JSON file: ' + err.message);
  }
  e.target.value = '';
});

btnClearCmp.addEventListener('click', () => {
  compareAnnotations = [];
  btnClearCmp.style.display = 'none';
  render();
});

// ── Auto-save ─────────────────────────────────────────────────
function autosave() {
  if (!currentCase || !annotatorName) return;
  localStorage.setItem(lsAnnsKey(currentCase, annotatorName), JSON.stringify(annotations));
}

// ── Warning helpers ───────────────────────────────────────────
function showWarning(msg) {
  warningBar.textContent = msg;
  warningBar.style.display = 'block';
  clearTimeout(warningBar._timeout);
  warningBar._timeout = setTimeout(hideWarning, 4000);
}
function hideWarning() { warningBar.style.display = 'none'; }
