const API = 'https://local.jmw.nz:41443/haptic';

const HOVER_SELECTORS = 'a, button, input, select, textarea, [role="button"], [role="link"], [role="menuitem"], [role="tab"], label';
const HOVER_THROTTLE_MS = 120;

let enabled = true;
let lastHover = 0;

function trigger(waveform) {
  if (!enabled) return;
  fetch(`${API}/${waveform}`, { method: 'POST', body: '' }).catch(() => {});
}

document.addEventListener('mousedown', () => {
  trigger('subtle_collision');
}, true);

document.addEventListener('mouseenter', (e) => {
  if (!e.target.closest(HOVER_SELECTORS)) return;
  const now = Date.now();
  if (now - lastHover < HOVER_THROTTLE_MS) return;
  lastHover = now;
  trigger('damp_collision');
}, true);

chrome.storage.sync.get({ enabled: true }, (data) => {
  enabled = data.enabled;
});

chrome.storage.onChanged.addListener((changes) => {
  if (changes.enabled) enabled = changes.enabled.newValue;
});

