'use strict';

// ── Label definitions ─────────────────────────────────────────
const LABELS = {
  1:  { name: 'ABD_SELECTIVE',  color: '#FF4D4D', lightText: false },
  2:  { name: 'ABD_CREATIVE',   color: '#FF7043', lightText: false },
  3:  { name: 'ABD_CAUSAL',     color: '#FF9800', lightText: true  },
  4:  { name: 'ABD_VISUAL',     color: '#FFC107', lightText: true  },
  5:  { name: 'IND_PATTERN',    color: '#66BB6A', lightText: false },
  6:  { name: 'IND_INTUITION',  color: '#26A69A', lightText: false },
  7:  { name: 'IND_BAYESIAN',   color: '#29B6F6', lightText: true  },
  8:  { name: 'IND_CASEBASED',  color: '#42A5F5', lightText: false },
  9:  { name: 'DED_HYPOTHETICO',color: '#AB47BC', lightText: false },
  10: { name: 'DED_ALGORITHMIC',color: '#7E57C2', lightText: false },
  11: { name: 'DED_HIERARCHICAL',color:'#5C6BC0', lightText: false },
  12: { name: 'DED_VALIDATION', color: '#3F51B5', lightText: false },
};

// ── State ─────────────────────────────────────────────────────
let rawText       = '';
let activeLabel   = null;
let annotations   = [];       // own annotations
let compareAnnotations = [];  // imported (read-only)
let currentCase   = '';
let annotatorName = '';
let pocRange      = null;     // {start, end} char range of PoC section
let popupAnnId    = null;

// ── DOM refs ──────────────────────────────────────────────────
const caseSelect    = document.getElementById('case-select');
const annotatorInput= document.getElementById('annotator-input');
const doc           = document.getElementById('doc');
const docPlaceholder= document.getElementById('doc-placeholder');
const annList       = document.getElementById('annotation-list');
const statsBar      = document.getElementById('stats-bar');
const jsonPreview   = document.getElementById('json-preview');
const warningBar    = document.getElementById('warning-bar');
const spanPopup     = document.getElementById('span-popup');
const popupLabelName= document.getElementById('popup-label-name');
const popupDelete   = document.getElementById('popup-delete');
const btnClearCmp   = document.getElementById('btn-clear-compare');

// ── Boot ──────────────────────────────────────────────────────
(async () => {
  const res  = await fetch('/api/cases');
  const list = await res.json();
  list.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f; opt.textContent = f;
    caseSelect.appendChild(opt);
  });
})();

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
        `Active: ${n} · ${LABELS[n].name}`;
    }
  });
});

// ── Case / annotator change ───────────────────────────────────
caseSelect.addEventListener('change', () => {
  currentCase = caseSelect.value;
  if (currentCase && annotatorName) loadCase();
});
annotatorInput.addEventListener('input', () => {
  annotatorName = annotatorInput.value.trim();
  if (currentCase && annotatorName) loadCase();
});

async function loadCase() {
  const res = await fetch(`/api/cases/${encodeURIComponent(currentCase)}`);
  rawText = await res.text();
  pocRange = detectPocRange(rawText);

  // Try to restore from localStorage
  const saved = localStorage.getItem(lsKey());
  if (saved) {
    const parsed = JSON.parse(saved);
    if (parsed.length > 0) {
      const resume = confirm(`Resume previous session? (${parsed.length} annotation(s) found)`);
      annotations = resume ? parsed : [];
    } else {
      annotations = [];
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

function lsKey() {
  return `annotations_${currentCase}_${annotatorName}`;
}

// ── PoC range detection ───────────────────────────────────────
// Returns {start, end} char positions of the PoC section in rawText
function detectPocRange(text) {
  const pocRe = /^##\s+Presentation of Case/im;
  const nextSecRe = /^##\s+/gm;

  const pocMatch = pocRe.exec(text);
  if (!pocMatch) return null;

  const start = pocMatch.index;
  nextSecRe.lastIndex = start + pocMatch[0].length;
  const nextMatch = nextSecRe.exec(text);
  const end = nextMatch ? nextMatch.index : text.length;
  return { start, end };
}

// ── Render document ───────────────────────────────────────────
function render() {
  // Merge own + compare annotations to build highlight map
  const allAnns = [
    ...annotations.map(a => ({ ...a, isCompare: false })),
    ...compareAnnotations.map(a => ({ ...a, isCompare: true })),
  ];

  // Build sorted boundary events
  const events = [];
  allAnns.forEach(a => {
    events.push({ pos: a.start, type: 'open',  ann: a });
    events.push({ pos: a.end,   type: 'close', ann: a });
  });
  events.sort((a, b) => a.pos - b.pos || (a.type === 'close' ? -1 : 1));

  let html = '';
  let i    = 0;
  let eIdx = 0;
  const open = new Set();

  while (i < rawText.length || eIdx < events.length) {
    // Flush any events at position i
    while (eIdx < events.length && events[eIdx].pos <= i) {
      const ev = events[eIdx++];
      if (ev.type === 'close') {
        if (open.has(ev.ann.id)) {
          open.delete(ev.ann.id);
          html += '</span>';
        }
      } else {
        open.add(ev.ann.id);
        const cls = ev.ann.isCompare ? 'hl compare' : 'hl';
        html += `<span class="${cls}" data-id="${ev.ann.id}" data-label="${ev.ann.label}">`;
      }
    }
    if (i >= rawText.length) break;

    const nextEvent = eIdx < events.length ? events[eIdx].pos : rawText.length;
    const chunk = rawText.slice(i, nextEvent);
    html += encodeChunk(chunk, i);
    i = nextEvent;
  }
  // Close any still-open spans
  open.forEach(() => { html += '</span>'; });

  // Wrap PoC zone
  if (pocRange) {
    // We inject a wrapper around the PoC region; do this post-hoc on the HTML string
    // by marking it at render time — simpler: we handle it in encodeChunk by tracking position
  }

  doc.innerHTML = html;
  wrapPocZone();
  attachHighlightListeners();
  renderPanel();
}

// Encode a text chunk into HTML, handling headers and PoC zone
function encodeChunk(chunk, startPos) {
  // Split into lines, process each
  const parts = chunk.split('\n');
  let out = '';
  let localPos = startPos;

  parts.forEach((line, idx) => {
    // Determine if this line is in PoC zone
    const inPoc = pocRange && localPos >= pocRange.start && localPos < pocRange.end;

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
    localPos += line.length + 1; // +1 for the \n
  });
  return out;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// Post-process: wrap the PoC region's DOM nodes in a .poc-zone div
function wrapPocZone() {
  if (!pocRange) return;

  // Walk text nodes and mark which ones fall inside pocRange
  const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let charPos = 0;
  const toWrap = []; // collect elements that are headers inside PoC range
  // Simpler approach: wrap the whole PoC block by inserting a div after render.
  // We find the md-h2 spans for "Presentation of Case" and wrap until the next md-h2.

  const spans = Array.from(doc.querySelectorAll('.md-h2, .md-h3'));
  let pocStart = null;
  let pocEnd   = null;
  for (let i = 0; i < spans.length; i++) {
    if (spans[i].textContent.match(/Presentation of Case/i)) {
      pocStart = spans[i];
      pocEnd   = spans[i + 1] || null; // next section header
      break;
    }
  }
  if (!pocStart) return;

  // Collect all nodes between pocStart (inclusive) and pocEnd (exclusive)
  const wrapDiv = document.createElement('div');
  wrapDiv.className = 'poc-zone';

  const parent = pocStart.parentNode;
  let node = pocStart;
  const nodesToMove = [];

  while (node && node !== pocEnd) {
    nodesToMove.push(node);
    node = node.nextSibling;
  }
  // Insert wrapDiv before pocStart
  parent.insertBefore(wrapDiv, pocStart);
  nodesToMove.forEach(n => wrapDiv.appendChild(n));
}

// ── Char offset computation ───────────────────────────────────
// Given a DOM node and offset within that node, return
// the absolute character position in rawText.
function getAbsoluteOffset(node, nodeOffset) {
  const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT);
  let pos = 0;
  let cur = walker.nextNode();
  while (cur) {
    if (cur === node) return pos + nodeOffset;
    pos += cur.textContent.length;
    cur = walker.nextNode();
  }
  return pos + nodeOffset;
}

// ── Mouse selection → annotation ─────────────────────────────
doc.addEventListener('mouseup', () => {
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed) return;

  if (!activeLabel) {
    showWarning('Select a label from the palette first.');
    sel.removeAllRanges();
    return;
  }
  if (!annotatorName) {
    showWarning('Enter your annotator name first.');
    sel.removeAllRanges();
    return;
  }

  const range = sel.getRangeAt(0);
  const start = getAbsoluteOffset(range.startContainer, range.startOffset);
  const end   = getAbsoluteOffset(range.endContainer,   range.endOffset);

  if (start >= end) { sel.removeAllRanges(); return; }

  // Check PoC zone
  if (pocRange && start < pocRange.end && end > pocRange.start) {
    showWarning('⚠ The Presentation of Case section cannot be annotated.');
    sel.removeAllRanges();
    return;
  }

  // Check overlap with own annotations
  const overlap = annotations.find(a => start < a.end && end > a.start);
  if (overlap) {
    showWarning('⚠ This selection overlaps an existing annotation — delete it first.');
    sel.removeAllRanges();
    return;
  }

  hideWarning();
  const text = rawText.slice(start, end);
  const id = 'a' + Date.now() + Math.random().toString(36).slice(2,6);
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
      const id = el.dataset.id;
      popupAnnId = id;
      const ann = annotations.find(a => a.id === id);
      if (!ann) return;
      popupLabelName.textContent = `${ann.label} · ${ann.label_name}`;
      spanPopup.style.display = 'flex';
      const rect = el.getBoundingClientRect();
      spanPopup.style.left = `${rect.left}px`;
      spanPopup.style.top  = `${rect.top - 40}px`;
    });
  });
}

document.addEventListener('click', e => {
  if (!spanPopup.contains(e.target)) {
    spanPopup.style.display = 'none';
    popupAnnId = null;
  }
});

popupDelete.addEventListener('click', () => {
  if (popupAnnId) removeAnnotation(popupAnnId);
  spanPopup.style.display = 'none';
  popupAnnId = null;
});

// ── Remove annotation ─────────────────────────────────────────
function removeAnnotation(id) {
  annotations = annotations.filter(a => a.id !== id);
  autosave();
  render();
}

// ── Right panel ───────────────────────────────────────────────
function renderPanel() {
  // Stats
  const ownCount = annotations.length;
  const cmpCount = compareAnnotations.length;
  if (cmpCount > 0) {
    const other = compareAnnotations[0]?.annotator || 'other';
    statsBar.textContent = `You: ${ownCount} span(s)  ·  ${other}: ${cmpCount} span(s)`;
  } else {
    statsBar.textContent = `${ownCount} annotation(s)`;
  }

  // Cards — own first, then compare
  const allCards = [
    ...annotations.map(a => ({ ...a, isCompare: false })),
    ...compareAnnotations.map(a => ({ ...a, isCompare: true })),
  ].sort((a, b) => a.start - b.start);

  annList.innerHTML = '';
  allCards.forEach(ann => {
    const lbl = LABELS[ann.label];
    const card = document.createElement('div');
    card.className = 'ann-card';
    card.style.borderLeftColor = lbl.color;

    const header = document.createElement('div');
    header.className = 'ann-card-header';

    const badge = document.createElement('span');
    badge.className = 'ann-badge' + (lbl.lightText ? ' light-text' : '');
    badge.style.background = lbl.color;
    badge.textContent = `${ann.label} · ${lbl.name}`;
    header.appendChild(badge);

    if (!ann.isCompare) {
      const del = document.createElement('button');
      del.className = 'ann-delete-btn';
      del.textContent = '✕';
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

    const excerpt = document.createElement('div');
    excerpt.className = 'ann-excerpt';
    excerpt.textContent = '"' + ann.text.replace(/\n/g,' ').slice(0, 90) + (ann.text.length > 90 ? '…' : '') + '"';
    card.appendChild(excerpt);

    const range = document.createElement('div');
    range.className = 'ann-range';
    range.textContent = `chars ${ann.start}–${ann.end}`;
    card.appendChild(range);

    annList.appendChild(card);
  });

  // JSON preview
  const payload = buildExportPayload();
  jsonPreview.textContent = JSON.stringify(payload.annotations, null, 2);
}

// ── Export ────────────────────────────────────────────────────
document.getElementById('btn-export').addEventListener('click', exportJSON);

function buildExportPayload() {
  return {
    case: currentCase,
    annotator: annotatorName,
    exported_at: new Date().toISOString(),
    annotations: annotations.map(({ id, start, end, label, label_name, text }) =>
      ({ id, start, end, label, label_name, text })),
  };
}

function exportJSON() {
  if (!currentCase) { alert('Load a case first.'); return; }
  const payload = buildExportPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  const safeName = currentCase.replace(/\.md$/, '').replace(/\s+/g, '_');
  a.download = `${safeName}_${annotatorName || 'anon'}.json`;
  a.click();
}

// ── Import (comparison) ───────────────────────────────────────
document.getElementById('import-file').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    compareAnnotations = (data.annotations || []).map(a => ({
      ...a,
      annotator: data.annotator || 'other',
      isCompare: true,
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
  localStorage.setItem(lsKey(), JSON.stringify(annotations));
}

// ── Warning helpers ───────────────────────────────────────────
function showWarning(msg) {
  warningBar.textContent = msg;
  warningBar.style.display = 'block';
  clearTimeout(warningBar._timeout);
  warningBar._timeout = setTimeout(hideWarning, 4000);
}
function hideWarning() {
  warningBar.style.display = 'none';
}
