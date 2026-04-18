const API = 'https://local.jmw.nz:41443/haptic';
const queue = [];
let busy = false;

async function drain() {
  if (busy) return;
  busy = true;
  while (queue.length) {
    const waveform = queue.shift();
    try { await fetch(`${API}/${waveform}`, { method: 'POST', body: '' }); } catch {}
    if (queue.length) await new Promise(r => setTimeout(r, 50));
  }
  busy = false;
}

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'haptic') {
    queue.push(message.waveform);
    drain();
  }
});
