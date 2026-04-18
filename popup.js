const WAVEFORMS = [
  'subtle_collision', 'damp_collision', 'sharp_collision', 'damp_state_change',
  'sharp_state_change', 'completed', 'happy_alert', 'mad', 'angry_alert',
  'firework', 'wave', 'square', 'knock', 'ringing', 'jingle',
];

const EVENTS = ['hoverLink', 'hoverButton', 'hoverInput', 'focus', 'submit', 'formError', 'slider', 'animation', 'scrollEdge'];

const DEFAULTS = {
  enabled: true,
  hoverLink:   { enabled: true,  waveform: 'damp_collision' },
  hoverButton: { enabled: true,  waveform: 'subtle_collision' },
  hoverInput:  { enabled: false, waveform: 'subtle_collision' },
  focus:       { enabled: true,  waveform: 'subtle_collision' },
  submit:      { enabled: true,  waveform: 'completed' },
  formError:   { enabled: true,  waveform: 'angry_alert' },
  scrollEdge:  { enabled: true,  waveform: 'sharp_collision' },
  slider:      { enabled: true,  waveform: 'damp_state_change' },
  animation:   { enabled: true,  waveform: 'subtle_collision' },
};

// Populate waveform dropdowns
EVENTS.forEach(ev => {
  const sel = document.getElementById(`wf-${ev}`);
  if (!sel) return;
  WAVEFORMS.forEach(wf => {
    const opt = document.createElement('option');
    opt.value = wf;
    opt.textContent = wf.replace(/_/g, ' ');
    sel.appendChild(opt);
  });
});

// Load settings
chrome.storage.sync.get(DEFAULTS, (data) => {
  document.getElementById('masterToggle').checked = data.enabled;
  EVENTS.forEach(ev => {
    const enEl = document.getElementById(`en-${ev}`);
    const wfEl = document.getElementById(`wf-${ev}`);
    if (enEl) enEl.checked = data[ev].enabled;
    if (wfEl) {
      wfEl.value = data[ev].waveform;
      wfEl.disabled = !data[ev].enabled;
    }
  });
});

// Master toggle
document.getElementById('masterToggle').addEventListener('change', (e) => {
  chrome.storage.sync.set({ enabled: e.target.checked });
});

// Per-event toggles and waveform selects
EVENTS.forEach(ev => {
  const enEl = document.getElementById(`en-${ev}`);
  const wfEl = document.getElementById(`wf-${ev}`);

  enEl?.addEventListener('change', () => {
    chrome.storage.sync.get(DEFAULTS, (data) => {
      const updated = { ...data[ev], enabled: enEl.checked };
      if (wfEl) wfEl.disabled = !enEl.checked;
      chrome.storage.sync.set({ [ev]: updated });
    });
  });

  wfEl?.addEventListener('change', () => {
    chrome.storage.sync.get(DEFAULTS, (data) => {
      const updated = { ...data[ev], waveform: wfEl.value };
      chrome.storage.sync.set({ [ev]: updated });
      fetch(`https://local.jmw.nz:41443/haptic/${wfEl.value}`, { method: 'POST', body: '' }).catch(() => {});
    });
  });
});

// Connection status
const dot = document.getElementById('dot');
const statusText = document.getElementById('statusText');

fetch('https://local.jmw.nz:41443/')
  .then(r => r.json())
  .then(data => {
    dot.classList.add('ok');
    statusText.textContent = `Connected · v${data.version}`;
  })
  .catch(() => {
    dot.classList.add('err');
    statusText.textContent = 'Plugin not running';
  });
