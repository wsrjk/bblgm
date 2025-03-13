from flask import Flask, render_template_string, request, jsonify
import random
import string
import time
import threading
import os

app = Flask(__name__)

bubbles = []
score = 0
level = 1
speed = 4
spawn_rate = 1.0
player_name = ""
highest_score = 0

# Generate bubbles periodically based on the current level
def generate_bubbles():
    global level, spawn_rate
    while True:
        if len(bubbles) < 10:
            x = random.randint(5, 95)
            if level <= 10:
                letter = random.choice(string.ascii_uppercase)
            elif level <= 15:
                letter = "".join(random.choices(string.ascii_uppercase, k=2))
            else:
                letter = "".join(random.choices(string.ascii_uppercase, k=3))

            if not any(abs(bubble['x'] - x) < 10 for bubble in bubbles):
                bubbles.append({
                    'id': int(time.time() * 1000),
                    'letter': letter,
                    'x': x,
                    'y': 700
                })
        time.sleep(spawn_rate)

threading.Thread(target=generate_bubbles, daemon=True).start()

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <title>Bubble Game - Level Mode</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                background-color: #bbdefb;
                overflow: hidden;
                margin: 0;
                font-family: Arial;
                height: 100vh;
                touch-action: manipulation;
            }
            .bubble {
                position: absolute;
                width: 8vw;
                height: 8vw;
                background-color: #42a5f5;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 4vw;
                box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
                transition: top 0.05s linear;
            }
            .highlight {
                background-color: #4caf50 !important;
            }
            .header {
                position: fixed;
                top: 10px;
                left: 0;
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
                box-sizing: border-box;
                font-size: 18px;
                font-weight: bold;
                color: #333;
            }
            .left {
                display: flex;
                gap: 20px;
            }
            .center {
                text-align: center;
                flex-grow: 1;
            }
            .right {
                display: flex;
                justify-content: flex-end;
            }
            .pause-btn {
                padding: 8px 12px;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            @media (min-width: 768px) {
                .bubble {
                    width: 60px;
                    height: 60px;
                    font-size: 26px;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <!-- Left side -->
            <div class="left">
                <div id="level">Level: 1</div>
                <div id="score">Score: 0</div>
                <div id="high-score">High Score: 0</div>
            </div>

            <!-- Center -->
            <div class="center">
                <span id="player-name">Player: Guest</span>
            </div>

            <!-- Right side -->
            <div class="right">
                <button class="pause-btn" onclick="togglePause()">Pause</button>
            </div>
        </div>

        <div id="game"></div>

        <audio id="correct-sound" src="/static/correct.mp3"></audio>
        <audio id="wrong-sound" src="/static/wrong.mp3"></audio>

        <script>
            let score = 0;
            let paused = false;
            let playerName = localStorage.getItem('playerName') || "";

            if (!playerName) {
                playerName = prompt("Enter player name:") || "Guest";
                localStorage.setItem('playerName', playerName);
            }
            document.getElementById('player-name').textContent = `Player: ${playerName}`;

            function updateBubbles(bubbles) {
                const game = document.getElementById('game');
                game.innerHTML = '';
                bubbles.forEach(bubble => {
                    const div = document.createElement('div');
                    div.className = 'bubble';
                    div.style.left = `${bubble.x}%`;
                    div.style.top = `${bubble.y}px`;
                    div.textContent = bubble.letter;

                    div.addEventListener('click', async () => {
                        await hitBubble(bubble.letter);
                    });

                    game.appendChild(div);
                });
            }

            async function fetchBubbles() {
                if (!paused) {
                    const response = await fetch('/get_bubbles');
                    const data = await response.json();
                    updateBubbles(data.bubbles);
                    document.getElementById('score').textContent = `Score: ${data.score}`;
                    document.getElementById('level').textContent = `Level: ${data.level}`;
                    document.getElementById('high-score').textContent = `High Score: ${data.highest_score}`;
                }
            }

            document.addEventListener('keydown', async (event) => {
                const keyPressed = event.key.toUpperCase();
                await hitBubble(keyPressed);
            });

            async function hitBubble(letter) {
                const response = await fetch(`/hit_bubble?letter=${letter}`);
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
                document.getElementById('level').textContent = `Level: ${data.level}`;
                document.getElementById('high-score').textContent = `High Score: ${data.highest_score}`;

                if (data.correct) {
                    document.getElementById('correct-sound').play();
                } else {
                    document.getElementById('wrong-sound').play();
                }
            }

            function togglePause() {
                paused = !paused;
            }

            setInterval(fetchBubbles, 50);
        </script>
    </body>
    </html>
    ''')

@app.route('/get_bubbles')
def get_bubbles():
    global bubbles, score, level, speed, spawn_rate, highest_score

    bubbles = [bubble for bubble in bubbles if bubble['y'] > -60]
    for bubble in bubbles:
        bubble['y'] -= speed

    if score >= level * 10 and level < 20:
        level += 1
        speed += 0.7
        spawn_rate = max(0.4, spawn_rate - 0.1)

    return jsonify({'bubbles': bubbles, 'score': score, 'level': level, 'highest_score': highest_score})

@app.route('/hit_bubble')
def hit_bubble():
    global bubbles, score, highest_score
    letter = request.args.get('letter')
    correct = False

    for bubble in bubbles[:]:
        if bubble['letter'] == letter:
            bubbles.remove(bubble)
            score += 1
            correct = True

    if score > highest_score:
        highest_score = score

    return jsonify({'bubbles': bubbles, 'score': score, 'level': level, 'highest_score': highest_score, 'correct': correct})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
