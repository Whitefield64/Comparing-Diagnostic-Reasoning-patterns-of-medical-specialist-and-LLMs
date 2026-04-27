'use strict';

const LS_SLOTS = 'cmp_slots_v2';

const LABELS = {
  ABD_SELECTIVE:    { color: '#FF4D4D', lightText: false },
  ABD_CREATIVE:     { color: '#FF7043', lightText: false },
  ABD_VISUAL:       { color: '#FF9800', lightText: true  },
  ABD_CAUSAL:       { color: '#FFC107', lightText: true  },
  DED_HYPOTHETICO:  { color: '#AB47BC', lightText: false },
  DED_ALGORITHMIC:  { color: '#7E57C2', lightText: false },
  DED_HIERARCHICAL: { color: '#5C6BC0', lightText: false },
  DED_VALIDATION:   { color: '#3F51B5', lightText: false },
  IND_PATTERN:      { color: '#66BB6A', lightText: false },
  IND_INTUITION:    { color: '#26A69A', lightText: false },
  IND_BAYESIAN:     { color: '#29B6F6', lightText: true  },
  IND_CASEBASED:    { color: '#42A5F5', lightText: false },
};

// Underline geometry — max 3 lines, fixed line-height
const LINE_H    = 1.5;              // px — line thickness
const LINE_GAP  = 2;                // px — gap between lines
const LINE_STEP = LINE_H + LINE_GAP; // 3.5px per layer
const LINE_LH   = 32;               // px — fixed line-height (fits 3 underlines with room to spare)

// Consensus config — overwritten by /api/config on load
let CONFIG = { consensus_min_votes: 5, consensus_min_agreement: 0.5 };

// slots[i] = { annotator, annotations, caseName, fileName }
const slots = [];
let caseText = '';

const fileInput  = document.getElementById('json-files-input');
const loadedFiles = document.getElementById('loaded-files');

// Load config then restore saved state
fetch('/api/config')
  .then(r => r.json())
  .then(cfg => { CONFIG = cfg; })
  .catch(() => {})
  .finally(() => restoreState());

/* ── File loading ───────────────────────────── */
fileInput.addEventListener('change', async e => {
  const files = [...e.target.files];
  if (!files.length) return;

  for (const file of files) {
    await loadAnnotationFile(file);
  }

  fileInput.value = '';
  persistState();
  updateStatus();
  renderLoadedFiles();
  if (slots.some(Boolean)) render();
});

function updateStatus() {
  const n = slots.filter(Boolean).length;
  document.getElementById('status').textContent = n
    ? `${n} file${n > 1 ? 's' : ''} loaded`
    : 'Load annotation files to begin';
}

async function loadAnnotationFile(file) {
  const data = JSON.parse(await file.text());
  const slot = {
    annotator: data.annotator,
    annotations: data.annotations,
    caseName: data.case,
    fileName: file.name,
  };

  const existingSlot = slots.find(Boolean);
  if (!caseText || !existingSlot) {
    const res = await fetch(`/api/text?case=${encodeURIComponent(data.case)}`);
    const json = await res.json();
    if (json.error) {
      document.getElementById('status').textContent = `Error: case text not found for "${data.case}"`;
      return;
    }
    caseText = json.text || '';
  } else if (existingSlot.caseName !== data.case) {
    document.getElementById('status').textContent = `Skipped ${file.name}: case does not match loaded document`;
    return;
  }

  if (slots.some(s => s && s.annotator === slot.annotator && s.caseName === slot.caseName)) return;

  slots.push(slot);
  renderLoadedFiles();
}

function removeLoadedFile(index) {
  if (index < 0 || index >= slots.length) return;
  slots.splice(index, 1);

  if (slots.length === 0) {
    caseText = '';
    closeDetail();
    document.getElementById('text-content').innerHTML = '–';
  }

  persistState();
  updateStatus();
  renderLoadedFiles();
  if (slots.length > 0) render();
}

/* ── Render ─────────────────────────────────── */
function render() {
  if (!caseText) return;

  const n   = caseText.length;
  const bps = new Set([0, n]);

  slots.forEach(slot => {
    if (!slot) return;
    slot.annotations.forEach(ann => {
      ann.ranges.forEach(([s, e]) => {
        bps.add(Math.max(0, s));
        bps.add(Math.min(n, e));
      });
    });
  });

  const sorted = [...bps].sort((a, b) => a - b);

  const segments = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    const start = sorted[i], end = sorted[i + 1];
    if (start >= end) continue;
    const mid = (start + end) >> 1;

    const covers = [];
    slots.forEach((slot, si) => {
      if (!slot) return;
      slot.annotations.forEach((ann, ai) => {
        if (ann.ranges.some(([s, e]) => s <= mid && mid < e)) covers.push({ si, ai });
      });
    });

    segments.push({ start, end, covers });
  }

  // Merge consecutive identical-cover segments
  const merged = [];
  for (const seg of segments) {
    const sig  = seg.covers.map(c => `${c.si}:${c.ai}`).join('|');
    const prev = merged[merged.length - 1];
    if (prev && prev.sig === sig) { prev.end = seg.end; }
    else merged.push({ ...seg, sig });
  }

  document.getElementById('text-content').style.lineHeight = LINE_LH + 'px';

  const buf = [];
  for (const seg of merged) {
    const text = renderMarkdownChunk(caseText.slice(seg.start, seg.end));

    if (seg.covers.length === 0) {
      buf.push(text);
      continue;
    }

    // Count label frequencies across all covers
    const freq = {};
    seg.covers.forEach(({ si, ai }) => {
      const name = slots[si].annotations[ai].label_name || 'UNKNOWN_LABEL';
      freq[name] = (freq[name] || 0) + 1;
    });

    const sortedLabels = Object.entries(freq).sort((a, b) => b[1] - a[1]);
    const top3         = sortedLabels.slice(0, 3).map(([name]) => name);
    const totalVotes   = seg.covers.length;
    const topCount     = sortedLabels[0][1];
    const agreement    = topCount / totalVotes;

    const isConsensus = totalVotes > CONFIG.consensus_min_votes
      && agreement > CONFIG.consensus_min_agreement;

    const style = buildStyle(top3, isConsensus);

    // Tooltip: label counts + consensus flag
    const titleParts = sortedLabels.map(([name, cnt]) => `${name} ×${cnt}`);
    if (isConsensus) titleParts.push('★ consensus');
    const title = titleParts.join('  |  ');

    const data = JSON.stringify(seg.covers);
    buf.push(`<span class="ann${isConsensus ? ' ann-consensus' : ''}" style="${style}" title="${esc(title)}" data-covers='${data}'>${text}</span>`);
  }

  document.getElementById('text-content').innerHTML = buf.join('');

  document.getElementById('text-content').onclick = e => {
    const span = e.target.closest('.ann');
    if (!span) { closeDetail(); return; }
    showDetail(JSON.parse(span.dataset.covers));
  };
}

/* ── Span styling ────────────────────────────── */
function buildStyle(top3, isConsensus) {
  const parts = [];

  if (isConsensus) {
    parts.push('background-color:rgba(100,116,139,0.13)');
  }

  if (top3.length > 0) {
    const N         = top3.length;
    const gradients = top3.map(name => `linear-gradient(${getLabelMeta(name).color},${getLabelMeta(name).color})`);
    const sizes     = top3.map(() => `100% ${LINE_H}px`);
    const positions = top3.map((_, i) => `0 calc(100% - ${(i * LINE_STEP).toFixed(1)}px)`);
    const pb        = ((N - 1) * LINE_STEP + LINE_H + 2).toFixed(1);

    parts.push(`background-image:${gradients.join(',')}`);
    parts.push(`background-size:${sizes.join(',')}`);
    parts.push(`background-position:${positions.join(',')}`);
    parts.push('background-repeat:no-repeat');
    parts.push(`padding-bottom:${pb}px`);
  }

  return parts.join(';');
}

/* ── Detail panel ────────────────────────────── */
function showDetail(covers) {
  const body = document.getElementById('detail-body');
  body.innerHTML = '';

  // Group by label for a summary header
  const freq = {};
  covers.forEach(({ si, ai }) => {
    const name = slots[si].annotations[ai].label_name || 'UNKNOWN_LABEL';
    freq[name] = (freq[name] || 0) + 1;
  });
  const total = covers.length;
  const topAgreement = Math.max(...Object.values(freq)) / total;

  const summary = document.createElement('div');
  summary.className = 'detail-summary';
  const chips = Object.entries(freq)
    .sort((a, b) => b[1] - a[1])
    .map(([name, cnt]) => {
      const { color } = getLabelMeta(name);
      return `<span class="detail-summary-chip" style="background:${color}">${esc(name)} <b>${cnt}</b></span>`;
    }).join('');
  summary.innerHTML = `<span class="detail-summary-meta">${total} annotation${total > 1 ? 's' : ''} · top agreement ${Math.round(topAgreement * 100)}%</span>${chips}`;
  body.appendChild(summary);

  // Individual cards
  covers.forEach(({ si, ai }) => {
    const slot      = slots[si];
    const ann       = slot.annotations[ai];
    const labelName = ann.label_name || 'UNKNOWN_LABEL';
    const meta      = getLabelMeta(labelName);
    const textColor = meta.lightText ? '#1f2937' : '#ffffff';

    const card = document.createElement('div');
    card.className = 'detail-card';
    card.style.borderLeft  = `3px solid ${meta.color}`;
    card.style.background  = toRgba(meta.color, 0.07);
    card.innerHTML = `
      <h4>${esc(slot.annotator)}</h4>
      <div class="label-bar" style="background:${meta.color};color:${textColor}">${esc(labelName)}</div>
      <pre>${esc(JSON.stringify(ann, null, 2))}</pre>
    `;
    body.appendChild(card);
  });

  document.getElementById('detail').style.display = '';
}

function closeDetail() {
  document.getElementById('detail').style.display = 'none';
}

document.getElementById('detail-close').addEventListener('click', closeDetail);

/* ── Detail panel resize ─────────────────────── */
(function () {
  const handle = document.getElementById('detail-resize-handle');
  const panel  = document.getElementById('detail');
  let startY, startH;

  handle.addEventListener('mousedown', e => {
    startY = e.clientY;
    startH = panel.offsetHeight;
    handle.classList.add('dragging');
    document.body.style.userSelect = 'none';

    function onMove(e) {
      const delta = startY - e.clientY;   // drag up = increase height
      const newH  = Math.min(Math.max(startH + delta, 80), window.innerHeight * 0.8);
      panel.style.height = newH + 'px';
    }

    function onUp() {
      handle.classList.remove('dragging');
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
})();

/* ── Persistence ─────────────────────────────── */
async function restoreState() {
  try {
    const raw = localStorage.getItem(LS_SLOTS);
    if (!raw) return;

    const saved = JSON.parse(raw);
    if (!Array.isArray(saved)) return;

    saved.forEach(s => { if (s) slots.push(s); });
    renderLoadedFiles();

    const first = slots.find(Boolean);
    if (!first?.caseName) return;

    const res  = await fetch(`/api/text?case=${encodeURIComponent(first.caseName)}`);
    const json = await res.json();
    caseText   = json.text || '';

    updateStatus();
    if (caseText) render();
  } catch (err) {
    console.error('Could not restore saved state:', err);
  }
}

function persistState() {
  try { localStorage.setItem(LS_SLOTS, JSON.stringify(slots)); }
  catch (err) { console.warn('Could not persist state:', err); }
}

/* ── Chip bar ────────────────────────────────── */
function renderLoadedFiles() {
  loadedFiles.innerHTML = '';

  slots.forEach((slot, index) => {
    const label = slot.annotator || slot.fileName || `File ${index + 1}`;
    const chip  = document.createElement('div');
    chip.className = 'loaded-file-chip';
    chip.title     = label;
    chip.innerHTML = `
      <span class="chip-index">${index + 1}</span>
      <button class="chip-remove" type="button" aria-label="Remove ${esc(label)}">×</button>
    `;
    chip.querySelector('.chip-remove').addEventListener('click', () => removeLoadedFile(index));
    loadedFiles.appendChild(chip);
  });

  const lbl = document.getElementById('load-jsons-label');
  lbl.classList.toggle('loaded', slots.length > 0);
  lbl.querySelector('.btn-label').textContent = slots.length ? `Load JSONs (+${slots.length})` : 'Load JSONs';
}

/* ── Utilities ───────────────────────────────── */
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderMarkdownChunk(chunk) {
  return chunk.split('\n').map((line, idx, arr) => {
    let out;
    if      (line.startsWith('### ')) out = `<span class="md-h3">${esc(line.slice(4))}</span>`;
    else if (line.startsWith('## '))  out = `<span class="md-h2">${esc(line.slice(3))}</span>`;
    else if (line.startsWith('# '))   out = `<span class="md-h1">${esc(line.slice(2))}</span>`;
    else                               out = esc(line);
    return idx < arr.length - 1 ? out + '\n' : out;
  }).join('');
}

function getLabelMeta(name) {
  return LABELS[name] || { color: '#64748b', lightText: false };
}

function toRgba(hex, alpha) {
  const b = parseInt(hex.replace('#',''), 16);
  return `rgba(${(b>>16)&255},${(b>>8)&255},${b&255},${alpha})`;
}
