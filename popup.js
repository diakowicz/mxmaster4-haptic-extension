const toggle = document.getElementById('toggle');
const dot = document.getElementById('dot');
const statusText = document.getElementById('statusText');

chrome.storage.sync.get({ enabled: true }, (data) => {
  toggle.checked = data.enabled;
});

toggle.addEventListener('change', () => {
  chrome.storage.sync.set({ enabled: toggle.checked });
});

fetch('https://local.jmw.nz:41443/', { method: 'GET' })
  .then(r => r.json())
  .then(data => {
    dot.classList.add('ok');
    statusText.textContent = `Connected (v${data.version})`;
  })
  .catch(() => {
    dot.classList.add('err');
    statusText.textContent = 'Plugin not running';
  });
