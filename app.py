from flask import Flask, render_template_string, request, jsonify
import random
import string
import time
import threading

app = Flask(__name__)

bubbles = []
score = 0
level = 1
speed = 4
spawn_rate = 1.0
player_name = ""
high_score = {"name": "Anonymous", "score": 0}

# Generate bubbles periodically based on the current level
def generate_bubbles():
    global level, spawn_rate
    while True:
        if len(bubbles) < 10:  # Limit total bubbles on screen
            letter = random.choice(string.ascii_uppercase)
            x = random.randint(5, 95)
            if not any(abs(bubble['x'] - x) < 10 for bubble in bubbles):
                bubbles.append({
                    'id': int(time.time() * 1000),
                    'letter': letter,
                    'x': x,
                    'y': 700  # Start from the bottom
                })
        time.sleep(spawn_rate)

# Start bubble generation in a separate thread
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
                z-index: 9999;
                transition: top 0.05s linear;
                box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
            }
            .score, .level, .high-score, .player {
                position: absolute;
                top: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            .score { left: 10px; }
            .level { left: 150px; }
            .high-score { left: 300px; }
            .player { right: 10px; }
            #start-screen {
                position: fixed;
                width: 100vw;
                height: 100vh;
                background-color: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                flex-direction: column;
                z-index: 10000;
            }
            #player-input {
                padding: 10px;
                font-size: 20px;
                margin-top: 10px;
                width: 60%;
                border-radius: 5px;
                border: none;
                outline: none;
                text-align: center;
            }
            #start-btn {
                margin-top: 20px;
                padding: 12px 24px;
                font-size: 20px;
                background-color: #42a5f5;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: 0.2s;
            }
            #start-btn:hover {
                background-color: #1e88e5;
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
        <div id="start-screen">
            <div>Enter Your Name:</div>
            <input id="player-input" type="text" placeholder="Your Name">
            <button id="start-btn" onclick="startGame()">Start Game</button>
        </div>

        <div class="score" id="score">Score: 0</div>
        <div class="level" id="level">Level: 1</div>
        <div class="high-score" id="high-score">High Score: 0</div>
        <div class="player" id="player-name">Player: Anonymous</div>
        <div id="game"></div>

        <script>
            let playerName = '';

            function startGame() {
                playerName = document.getElementById('player-input').value || 'Anonymous';
                document.getElementById('player-name').textContent = `Player: ${playerName}`;
                document.getElementById('start-screen').style.display = 'none';
                fetch(`/set_player_name?name=${playerName}`);
            }

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
                const response = await fetch('/get_bubbles');
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
                document.getElementById('level').textContent = `Level: ${data.level}`;
                document.getElementById('high-score').textContent = `High Score: ${data.high_score.name} - ${data.high_score.score}`;
            }

            async function hitBubble(letter) {
                const response = await fetch(`/hit_bubble?letter=${letter}`);
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
            }

            setInterval(fetchBubbles, 50);
        </script>
    </body>
    </html>
    ''')

@app.route('/set_player_name')
def set_player_name():
    global player_name
    player_name = request.args.get('name')
    return jsonify({'status': 'ok'})

@app.route('/get_bubbles')
def get_bubbles():
    global bubbles, score, level, speed, spawn_rate, high_score
    
    bubbles = [bubble for bubble in bubbles if bubble['y'] > -60]
    for bubble in bubbles:
        bubble['y'] -= speed
    
    if score >= level * 10 and level < 10:
        level += 1
        speed += 0.7
        spawn_rate = max(0.4, spawn_rate - 0.1)
    
    if score > high_score['score']:
        high_score['score'] = score
        high_score['name'] = player_name
    
    return jsonify({'bubbles': bubbles, 'score': score, 'level': level, 'high_score': high_score})

@app.route('/hit_bubble')
def hit_bubble():
    global bubbles, score
    letter = request.args.get('letter')
    for bubble in bubbles[:]:
        if bubble['letter'] == letter:
            bubbles.remove(bubble)
            score += 1
    return jsonify({'bubbles': bubbles, 'score': score, 'level': level})

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
