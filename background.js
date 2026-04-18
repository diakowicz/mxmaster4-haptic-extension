const API = 'https://local.jmw.nz:41443/haptic';

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === 'haptic') {
    fetch(`${API}/${message.waveform}`, { method: 'POST', body: '' }).catch(() => {});
  }
});
