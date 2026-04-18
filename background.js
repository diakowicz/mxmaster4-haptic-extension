const API = 'https://local.jmw.nz:41443/haptic';
const queue = [];
let busy = false;

async function drain() {
  if (busy) return;
  busy = true;
  while (queue.length) {
    const wf = queue.shift();
    try { await fetch(`${API}/${wf}`, { method: 'POST', body: '' }); } catch {}
    if (queue.length) await new Promise(r => setTimeout(r, 50));
  }
  busy = false;
}

chrome.runtime.onConnect.addListener((port) => {
  port.onMessage.addListener(({ waveform }) => {
    queue.push(waveform);
    drain();
  });
});
