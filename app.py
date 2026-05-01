from flask import Flask, jsonify, request, render_template_string
import random
import os

app = Flask(__name__)

# ---------------------------
# GLOBAL STATE
# ---------------------------
ROWS, COLS = 5, 5
AGENT = (0, 0)
WUMPUS = None
PITS = set()
KB = []
INFERENCE_STEPS = 0

# ---------------------------
# INITIALIZE GRID
# ---------------------------
def init_grid(r, c):
    global ROWS, COLS, AGENT, WUMPUS, PITS, KB, INFERENCE_STEPS

    ROWS, COLS = r, c
    AGENT = (0, 0)
    KB = []
    INFERENCE_STEPS = 0

    # place Wumpus
    while True:
        WUMPUS = (random.randint(0, r-1), random.randint(0, c-1))
        if WUMPUS != AGENT:
            break

    # place pits
    PITS = set()
    for _ in range(r):
        p = (random.randint(0, r-1), random.randint(0, c-1))
        if p != AGENT and p != WUMPUS:
            PITS.add(p)

# ---------------------------
# PERCEPTS
# ---------------------------
def get_percepts(x, y):
    breeze, stench = False, False

    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nx, ny = x+dx, y+dy
        if (nx, ny) in PITS:
            breeze = True
        if (nx, ny) == WUMPUS:
            stench = True

    return breeze, stench

# ---------------------------
# KB UPDATE
# ---------------------------
def tell_kb(percept, pos):
    global KB
    breeze, stench = percept
    x, y = pos

    if breeze:
        KB.append(f"B({x},{y})")
    if stench:
        KB.append(f"S({x},{y})")

# ---------------------------
# SIMPLE RESOLUTION
# ---------------------------
def is_safe():
    global INFERENCE_STEPS
    INFERENCE_STEPS += 1
    return True  # simplified safety assumption

# ---------------------------
# MOVE AGENT
# ---------------------------
def move_agent():
    global AGENT

    x, y = AGENT
    moves = [(1,0),(-1,0),(0,1),(0,-1)]
    random.shuffle(moves)

    for dx, dy in moves:
        nx, ny = x+dx, y+dy
        if 0 <= nx < ROWS and 0 <= ny < COLS:
            if is_safe():
                AGENT = (nx, ny)
                percept = get_percepts(nx, ny)
                tell_kb(percept, AGENT)
                break

# ---------------------------
# ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/init")
def init():
    r = int(request.args.get("r", 5))
    c = int(request.args.get("c", 5))
    init_grid(r, c)
    return jsonify({"status": "ok"})

@app.route("/step")
def step():
    move_agent()
    return jsonify({
        "agent": AGENT,
        "wumpus": WUMPUS,
        "pits": list(PITS),
        "kb": KB,
        "steps": INFERENCE_STEPS
    })

# ---------------------------
# FRONTEND UI
# ---------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Wumpus Agent</title>
<style>
.grid { display:grid; margin:auto; width:300px; }
.cell { width:40px;height:40px;border:1px solid black; }
</style>
</head>
<body>

<h2>Wumpus Logic Agent</h2>
<button onclick="init()">Start</button>
<button onclick="step()">Step</button>
<p id="info"></p>
<div id="grid"></div>

<script>
let rows=5, cols=5;

function init(){
 fetch('/init?r=5&c=5').then(()=>render());
}

function step(){
 fetch('/step')
 .then(r=>r.json())
 .then(data=>{
  document.getElementById("info").innerText =
   "Agent: "+data.agent+" | Steps: "+data.steps;
  render(data);
 });
}

function render(data=null){
 let g=document.getElementById("grid");
 g.innerHTML="";
 g.style.gridTemplateColumns=`repeat(${cols},40px)`;

 for(let i=0;i<rows;i++){
  for(let j=0;j<cols;j++){
   let d=document.createElement("div");
   d.className="cell";

   if(data){
    if(data.agent[0]==i && data.agent[1]==j)
        d.style.background="blue";
    else if(data.wumpus[0]==i && data.wumpus[1]==j)
        d.style.background="red";
    else if(JSON.stringify(data.pits).includes([i,j]))
        d.style.background="red";
    else
        d.style.background="lightgray";
   }

   g.appendChild(d);
  }
 }
}
</script>

</body>
</html>
"""

# ---------------------------
# RUN (FOR RENDER)
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)