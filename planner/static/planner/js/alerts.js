(() => {
  const alertList = document.getElementById('live-alerts');
  if (!alertList) {
    return;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/alerts/`);

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const item = document.createElement('li');
    item.className = 'sev-low';
    item.textContent = `[LIVE] ${data.title}: ${data.message}`;
    alertList.prepend(item);
  };
})();
