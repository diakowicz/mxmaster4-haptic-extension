const HOVER_THROTTLE_MS = 120;
const SCROLL_EDGE_PX = 40;
const SCROLL_COOLDOWN_MS = 600;

const SLIDER_STEP_PCT  = 5;    // fire haptic every 5% of slider range
const ANIM_THROTTLE_MS = 200;  // min ms between animation haptics per element

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

let settings = JSON.parse(JSON.stringify(DEFAULTS));
let lastHover = 0;
let lastScrollEdge = 0;

function trigger(waveform) {
  if (!settings.enabled) return;
  chrome.runtime.sendMessage({ type: 'haptic', waveform });
}

chrome.storage.sync.get(DEFAULTS, (data) => { settings = data; });
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'sync') return;
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

// Slider — fire every SLIDER_STEP_PCT% of range
const sliderLastPct = new WeakMap();
document.addEventListener('input', (e) => {
  if (!settings.slider?.enabled) return;
  const el = e.target;
  if (el.type !== 'range') return;
  const min = parseFloat(el.min) || 0;
  const max = parseFloat(el.max) || 100;
  const pct = ((parseFloat(el.value) - min) / (max - min)) * 100;
  const prev = sliderLastPct.get(el) ?? -999;
  if (Math.abs(pct - prev) >= SLIDER_STEP_PCT) {
    sliderLastPct.set(el, pct);
    trigger(settings.slider.waveform);
  }
}, true);

// CSS animation & transition end
const animLastFired = new WeakMap();
function onAnimEnd(e) {
  if (!settings.animation?.enabled) return;
  const now = Date.now();
  if (now - (animLastFired.get(e.target) ?? 0) < ANIM_THROTTLE_MS) return;
  animLastFired.set(e.target, now);
  trigger(settings.animation.waveform);
}
document.addEventListener('animationend',  onAnimEnd, true);
document.addEventListener('transitionend', onAnimEnd, true);

// Scroll to edge — no debounce (smooth-scroll fires continuously, debounce never fires)
document.addEventListener('scroll', (e) => {
  if (window.self !== window.top) return;
  const now = Date.now();
  if (now - lastScrollEdge < SCROLL_COOLDOWN_MS) return;
  const el = (e.target === document || e.target === document.documentElement)
    ? document.documentElement : e.target;
  const atTop = el.scrollTop <= SCROLL_EDGE_PX;
  const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - SCROLL_EDGE_PX;
  if (!atTop && !atBottom) return;
  lastScrollEdge = now;
  chrome.storage.sync.get(DEFAULTS, (s) => {
    if (!s.enabled || !s.scrollEdge.enabled) return;
    trigger(s.scrollEdge.waveform);
  });
}, { passive: true, capture: true });
