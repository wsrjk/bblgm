from flask import Flask, render_template_string, request, jsonify
import random
import string
import time
import threading

app = Flask(__name__)

bubbles = []
score = 0
level = 1
speed = 4  # Increased starting speed
spawn_rate = 1.0  # Faster spawn rate

# Generate bubbles periodically based on the current level
def generate_bubbles():
    global level, spawn_rate
    while True:
        if len(bubbles) < 10:  # Limit total bubbles on screen
            letter = random.choice(string.ascii_uppercase)
            x = random.randint(5, 95)
            # Ensure proper horizontal spacing between bubbles
            if not any(abs(bubble['x'] - x) < 10 for bubble in bubbles):
                bubbles.append({
                    'id': int(time.time() * 1000),
                    'letter': letter,
                    'x': x,
                    'y': 700  # Start from the bottom (increased starting point)
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
            .score, .level {
                position: absolute;
                top: 10px;
                left: 10px;
                font-size: 24px;
                font-weight: bold;
            }
            .level {
                left: auto;
                right: 10px;
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
        <div class="score" id="score">Score: 0</div>
        <div class="level" id="level">Level: 1</div>
        <div id="game"></div>

        <script>
            function updateBubbles(bubbles) {
                const game = document.getElementById('game');
                game.innerHTML = '';
                bubbles.forEach(bubble => {
                    const div = document.createElement('div');
                    div.className = 'bubble';
                    div.style.left = `${bubble.x}%`;
                    div.style.top = `${bubble.y}px`;
                    div.textContent = bubble.letter;

                    // ✅ Touch support for mobile
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
            }

            // ✅ Keyboard support
            document.addEventListener('keydown', async (event) => {
                const keyPressed = event.key.toUpperCase();
                await hitBubble(keyPressed);
            });

            // ✅ Function to hit bubbles
            async function hitBubble(letter) {
                const response = await fetch(`/hit_bubble?letter=${letter}`);
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
                document.getElementById('level').textContent = `Level: ${data.level}`;
            }

            setInterval(fetchBubbles, 50);
        </script>
    </body>
    </html>
    ''')

@app.route('/get_bubbles')
def get_bubbles():
    global bubbles, score, level, speed, spawn_rate
    
    # Remove bubbles once they go out of view
    bubbles = [bubble for bubble in bubbles if bubble['y'] > -60]
    
    # Move bubbles upward (increased speed for better flow)
    for bubble in bubbles:
        bubble['y'] -= speed
    
    # ✅ Level progression
    if score >= level * 10 and level < 10:
        level += 1
        speed += 0.7  # Increase bubble speed with each level
        spawn_rate = max(0.4, spawn_rate - 0.1)  # Increase bubble generation speed
    
    return jsonify({'bubbles': bubbles, 'score': score, 'level': level})

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
