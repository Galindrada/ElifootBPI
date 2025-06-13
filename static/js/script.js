document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const startBtn = document.getElementById('start-fixture-btn');
    const nextBtn = document.getElementById('next-fixture-btn');
    const matchLogList = document.getElementById('match-log');
    const clock = document.getElementById('minute-clock');

    function addLogMessage(message) {
        const item = document.createElement('li');
        item.textContent = message;
        matchLogList.appendChild(item);
        matchLogList.parentElement.scrollTop = matchLogList.parentElement.scrollHeight;
    }

    // --- Socket Event Listeners ---
    socket.on('connect', () => {
        console.log('Connected to server!');
    });

    socket.on('log_message', (msg) => {
        addLogMessage(msg.data);
    });

    socket.on('minute_update', (data) => {
        // Update clock
        if (clock) {
            clock.textContent = data.minute;
        }

        // Update scores for all matches
        for (const matchId in data.scores) {
            const scoreElement = document.getElementById(`score-${matchId}`);
            if (scoreElement) {
                const score = data.scores[matchId];
                scoreElement.textContent = `${score.home} - ${score.away}`;
            }
        }
    });

    socket.on('fixture_finished', () => {
        if(startBtn) startBtn.style.display = 'none';
        if(nextBtn) nextBtn.style.display = 'inline-block';
        addLogMessage('Navigate to the next fixture when ready.');
    });

    // --- DOM Event Listeners ---
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            console.log('Requesting to start fixture simulation...');
            startBtn.disabled = true;
            startBtn.textContent = 'Simulating...';
            
            // Clear previous log messages
            matchLogList.innerHTML = '';
            addLogMessage('Starting simulation...');
            
            socket.emit('start_fixture_simulation', {});
        });
    }
});

