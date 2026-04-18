const HOVER_THROTTLE_MS = 120;
const SCROLL_EDGE_PX = 8;
const SCROLL_COOLDOWN_MS = 600;

const DEFAULTS = {
  enabled: true,
  hoverLink:   { enabled: true,  waveform: 'damp_collision' },
  hoverButton: { enabled: true,  waveform: 'subtle_collision' },
  hoverInput:  { enabled: false, waveform: 'subtle_collision' },
  focus:       { enabled: true,  waveform: 'subtle_collision' },
  submit:      { enabled: true,  waveform: 'completed' },
  formError:   { enabled: true,  waveform: 'angry_alert' },
  scrollEdge:  { enabled: true,  waveform: 'sharp_collision' },
};

let settings = JSON.parse(JSON.stringify(DEFAULTS));
let lastHover = 0;
let lastScrollEdge = 0;

function trigger(waveform) {
  if (!settings.enabled) return;
  chrome.runtime.sendMessage({ type: 'haptic', waveform });
}

chrome.storage.sync.get(DEFAULTS, (data) => { settings = data; });
chrome.storage.onChanged.addListener((changes) => {
  for (const key in changes) settings[key] = changes[key].newValue;
});

// Hover — different waveform per element type
document.addEventListener('mouseenter', (e) => {
  const now = Date.now();
  if (now - lastHover < HOVER_THROTTLE_MS) return;
  const t = e.target;

  if (settings.hoverLink.enabled && t.closest('a[href]')) {
    lastHover = now;
    trigger(settings.hoverLink.waveform);
  } else if (settings.hoverButton.enabled && t.closest('button, [role="button"], [role="menuitem"], [role="tab"]')) {
    lastHover = now;
    trigger(settings.hoverButton.waveform);
  } else if (settings.hoverInput.enabled && t.closest('input, select, textarea, label')) {
    lastHover = now;
    trigger(settings.hoverInput.waveform);
  }
}, true);

// Focus on form fields
document.addEventListener('focus', (e) => {
  if (!settings.focus.enabled) return;
  if (e.target.matches('input:not([type="hidden"]), select, textarea')) {
    trigger(settings.focus.waveform);
  }
}, true);

// Form submit
document.addEventListener('submit', () => {
  if (!settings.submit.enabled) return;
  trigger(settings.submit.waveform);
}, true);

// Form validation error
document.addEventListener('invalid', () => {
  if (!settings.formError.enabled) return;
  trigger(settings.formError.waveform);
}, true);

// Scroll to edge
let scrollTimer;
window.addEventListener('scroll', () => {
  if (!settings.scrollEdge.enabled) return;
  clearTimeout(scrollTimer);
  scrollTimer = setTimeout(() => {
    const now = Date.now();
    if (now - lastScrollEdge < SCROLL_COOLDOWN_MS) return;
    const atTop = window.scrollY <= SCROLL_EDGE_PX;
    const atBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - SCROLL_EDGE_PX;
    if (atTop || atBottom) {
      lastScrollEdge = now;
      trigger(settings.scrollEdge.waveform);
    }
  }, 60);
}, { passive: true });
