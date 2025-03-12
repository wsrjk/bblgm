from flask import Flask, render_template_string, request, jsonify
import random
import string
import time
import threading

app = Flask(__name__)

bubbles = []
score = 0

# Generate bubbles periodically
def generate_bubbles():
    while True:
        letter = random.choice(string.ascii_uppercase)
        # Generate unique x position to avoid clustering
        x = random.randint(5, 95)  
        if not any(abs(bubble['x'] - x) < 10 for bubble in bubbles):
            bubbles.append({
                'id': int(time.time() * 1000),
                'letter': letter,
                'x': x,
                'y': 600  # Start from the bottom of the screen
            })
        time.sleep(1)

threading.Thread(target=generate_bubbles, daemon=True).start()

@app.route('/')
def index():
    return render_template_string('''
    <!doctype html>
    <html>
    <head>
        <title>Bubble Game</title>
        <style>
            body { background-color: #bbdefb; overflow: hidden; margin: 0; font-family: Arial; height: 100vh; }
            .bubble {
                position: absolute;
                width: 60px;
                height: 60px;
                background-color: #42a5f5;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 26px;
                z-index: 9999;
                transition: top 0.05s linear;
            }
            .score {
                position: absolute;
                top: 10px;
                left: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="score" id="score">Score: 0</div>
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
                    game.appendChild(div);
                });
            }

            async function fetchBubbles() {
                const response = await fetch('/get_bubbles');
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
            }

            document.addEventListener('keydown', async (event) => {
                const keyPressed = event.key.toUpperCase();
                const response = await fetch(`/hit_bubble?letter=${keyPressed}`);
                const data = await response.json();
                updateBubbles(data.bubbles);
                document.getElementById('score').textContent = `Score: ${data.score}`;
            });

            setInterval(fetchBubbles, 50);
        </script>
    </body>
    </html>
    ''')

@app.route('/get_bubbles')
def get_bubbles():
    global bubbles, score
    # Keep only bubbles that are still on the screen
    bubbles = [bubble for bubble in bubbles if bubble['y'] > -60]
    for bubble in bubbles:
        bubble['y'] -= 2  # Move upward smoothly
    return jsonify({'bubbles': bubbles, 'score': score})

@app.route('/hit_bubble')
def hit_bubble():
    global bubbles, score
    letter = request.args.get('letter')
    for bubble in bubbles[:]:
        if bubble['letter'] == letter:
            bubbles.remove(bubble)
            score += 1
    return jsonify({'bubbles': bubbles, 'score': score})

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
