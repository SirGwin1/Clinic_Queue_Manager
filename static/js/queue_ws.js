const storage = window.localStorage;
const soundToggleBtn = document.getElementById('soundToggleBtn');
const browserNotifyBtn = document.getElementById('browserNotifyBtn');
let soundEnabled = storage.getItem('queue-sound-enabled') === 'true';

function updateSoundButton() {
    if (soundToggleBtn) {
        soundToggleBtn.textContent = soundEnabled ? 'Sound: On' : 'Sound: Off';
        soundToggleBtn.classList.toggle('btn-light', soundEnabled);
        soundToggleBtn.classList.toggle('btn-outline-light', !soundEnabled);
    }
}

function playAlertTone() {
    if (!soundEnabled) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const audioContext = new AudioContext();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = 760;
    gainNode.gain.value = 0.05;
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.14);
}

if (soundToggleBtn) {
    updateSoundButton();
    soundToggleBtn.addEventListener('click', () => {
        soundEnabled = !soundEnabled;
        storage.setItem('queue-sound-enabled', String(soundEnabled));
        updateSoundButton();
    });
}

if (browserNotifyBtn) {
    browserNotifyBtn.addEventListener('click', async () => {
        if (!('Notification' in window)) {
            browserNotifyBtn.textContent = 'Browser alerts unsupported';
            return;
        }
        const permission = await Notification.requestPermission();
        browserNotifyBtn.textContent = permission === 'granted' ? 'Alerts enabled' : 'Alerts blocked';
    });
}

const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const websocketUrl = `${protocol}://${window.location.host}/ws/notifications/`;
let socket;

function connectWebSocket() {
    socket = new WebSocket(websocketUrl);
    socket.onopen = () => {
        const status = document.getElementById('connectionStatus');
        if (status) {
            status.textContent = 'Connected';
            status.className = 'badge bg-success';
        }
    };
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'connected') return;
        if (data.type === 'notification') {
            playAlertTone();
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Clinic Queue Manager', { body: data.message });
            }
            const message = document.createElement('div');
            message.className = 'alert alert-info mt-3';
            message.textContent = data.message;
            document.body.appendChild(message);
            setTimeout(() => message.remove(), 4000);
        }
    };
    socket.onclose = () => {
        const status = document.getElementById('connectionStatus');
        if (status) {
            status.textContent = 'Reconnecting';
            status.className = 'badge bg-warning text-dark';
        }
        setTimeout(connectWebSocket, 2000);
    };
    socket.onerror = () => {
        const status = document.getElementById('connectionStatus');
        if (status) {
            status.textContent = 'Connection error';
            status.className = 'badge bg-danger';
        }
    };
}

const status = document.createElement('div');
status.id = 'connectionStatus';
status.className = 'badge bg-success';
status.textContent = 'Connected';
const nav = document.querySelector('.navbar');
if (nav) {
    nav.appendChild(status);
}
connectWebSocket();
