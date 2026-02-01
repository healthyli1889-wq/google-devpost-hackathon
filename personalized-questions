"""
Personalized 4-question flow API + World discovery.
Serves: / (conversation), /worlds (world templates), /world/<slug> (enter a world).
Run: pip install flask flask-cors && python personalized_questions_api.py
Then open: http://127.0.0.1:5001/  or  http://127.0.0.1:5001/worlds
"""

import os
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

from flask_cors import CORS
CORS(app)

# World templates: slug -> display name and tagline (for enter page and API).
WORLD_DATA = {
    "neo-tokyo": {
        "name": "Neo-Tokyo 2099",
        "tagline": "A dense urban sprawl where corporate AI wars against rogue androids.",
        "genre": "Cyberpunk",
    },
    "velvet-manor": {
        "name": "Velvet Manor",
        "tagline": "A murder mystery where every NPC has a secret agenda.",
        "genre": "Mystery",
    },
    "sector-7": {
        "name": "Sector 7 Slums",
        "tagline": "Survive the low-life, high-tech underworld economy.",
        "genre": "Cyberpunk",
    },
    "eldoria": {
        "name": "Eldoria",
        "tagline": "High fantasy realm with dynamic magical ecosystems.",
        "genre": "Fantasy",
    },
    "dust-rust": {
        "name": "Dust & Rust",
        "tagline": "Resource scarcity simulation with raider factions.",
        "genre": "Post-Apoc",
    },
    "orbital-z": {
        "name": "Orbital Station Z",
        "tagline": "Zero-G simulation environment.",
        "genre": "Sci-Fi",
    },
    "abyss-colony": {
        "name": "Abyss Colony",
        "tagline": "Deep sea pressure and society sim.",
        "genre": "Aquatic",
    },
    "the-archives": {
        "name": "The Archives",
        "tagline": "Infinite knowledge retrieval agents.",
        "genre": "Academic",
    },
}

# First question is fixed; we personalize Q2, Q3, Q4 from previous answers.
QUESTION_1 = (
    "Do you seek to bring order to this world, or disruption?"
)

# Build next question from keywords in previous answers (understands intent).
def _keywords(answers):
    text = " ".join(answers).lower()
    return {
        "order": "order" in text or "structure" in text or "harmony" in text or "balance" in text,
        "disruption": "disruption" in text or "chaos" in text or "storm" in text,
        "mystery": "mystery" in text or "unknown" in text,
        "control": "control" in text or "power" in text or "influence" in text,
    }

def _response_and_next(question_index: int, answers: list) -> tuple[str, str]:
    """Return (short_response, next_question_text). answers are 0-indexed by order given."""
    k = _keywords(answers)
    last = (answers[-1].strip().lower() if answers else "") or "your path"

    if question_index == 1:
        # Just answered Q1 → give response + Q2
        if k["disruption"]:
            resp = f"You lean into change. '{last}' suggests you value momentum over stability."
            next_q = "What would you willing to sacrifice to keep that momentum—certainty, or connection?"
        elif k["order"]:
            resp = f"You lean toward stability. '{last}' suggests you value clarity and structure."
            next_q = "How do you want others to experience that structure—through rules, or through example?"
        elif k["mystery"]:
            resp = f"You embrace the unknown. '{last}' suggests you're comfortable without a fixed map."
            next_q = "When things get unclear, what do you rely on more—intuition, or evidence?"
        else:
            resp = f"Your choice—'{last}'—sets the tone for what follows."
            next_q = "What matters more to you right now: influence over others, or clarity over yourself?"
        return resp, next_q

    if question_index == 2:
        # Just answered Q2 → response + Q3
        if "certainty" in last or "connection" in last or "momentum" in last:
            resp = "That trade-off defines how you'll lead—or step back."
            next_q = "In this simulation, do you see yourself as the one making the rules, or the one testing their limits?"
        elif "rules" in last or "example" in last or "structure" in last:
            resp = "How you embody structure says a lot about the order you seek."
            next_q = "When someone challenges your approach, do you refine the system, or defend it first?"
        elif "intuition" in last or "evidence" in last:
            resp = "That preference shapes how you'll interpret everything that comes next."
            next_q = "If the simulation offered you one gift—insight or power—which would you take?"
        else:
            resp = "That distinction will matter as the simulation deepens."
            next_q = "Do you want this experience to change how you decide, or how you relate to others?"
        return resp, next_q

    if question_index == 3:
        # Just answered Q3 → response + Q4
        if "making the rules" in last or "testing" in last or "limits" in last:
            resp = "Your role—architect or provocateur—is becoming clear."
            next_q = "One last question: when this ends, what do you want to leave behind—a clear outcome, or an open question?"
        elif "refine" in last or "defend" in last or "system" in last:
            resp = "That reaction under pressure reveals a lot."
            next_q = "When this ends, what matters more—that something concrete was built, or that the process was honest?"
        elif "insight" in last or "power" in last or "gift" in last:
            resp = "Your choice of gift aligns with what you've shown so far."
            next_q = "At the end, would you rather have a single clear answer, or many possible ones?"
        else:
            resp = "That direction will shape the closing of the simulation."
            next_q = "What would make this experience feel complete for you—a result, or a new question to carry?"
        return resp, next_q

    # question_index == 4: last answer, no next question
    resp = (
        f"Your answer—'{last}'—closes the loop. "
        "The simulation has enough to reflect your influence. Thank you for defining it."
    )
    return resp, ""

@app.route("/")
def index():
    """Serve the conversation frontend so fetch() works (same origin)."""
    path = os.path.join(os.path.dirname(__file__), "google_frontend_progressbar_conversation.html")
    if not os.path.isfile(path):
        return (
            "<p>Frontend file not found. Put google_frontend_progressbar_conversation.html "
            "in the same folder as this script.</p>",
            404,
        )
    return send_file(path, mimetype="text/html")


@app.route("/next_question", methods=["POST"])
def next_question():
    """Body: { "question_index": 1|2|3|4, "answers": ["answer1", "answer2", ...] }."""
    try:
        data = request.get_json() or {}
        question_index = int(data.get("question_index", 1))
        answers = list(data.get("answers", []))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid question_index or answers"}), 400

    if question_index < 1 or question_index > 4:
        return jsonify({"error": "question_index must be 1–4"}), 400

    # Terminal output so you see each request
    print(f"  [API] Question {question_index}/4  answers: {answers!r}")

    response_text, next_question_text = _response_and_next(question_index, answers)

    out = {
        "response": response_text,
        "next_question": next_question_text,
        "question_index": question_index,
        "is_complete": question_index == 4,
    }
    return jsonify(out)


@app.route("/worlds")
def worlds():
    """Serve the world template discovery page (click into a world, then back)."""
    path = os.path.join(os.path.dirname(__file__), "google_frontend_page2_worldtemplate.html")
    if not os.path.isfile(path):
        return "<p>World template page not found.</p>", 404
    return send_file(path, mimetype="text/html")


def _world_entry_html(name: str, tagline: str, genre: str) -> str:
    """Minimal 'you entered this world' page with Back to Discover."""
    return f"""<!DOCTYPE html>
<html class="dark" lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{name} - Forger</title>
<link href="https://fonts.googleapis.com/css2?family=Spline+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#1c1022] text-white font-sans min-h-screen flex flex-col items-center justify-center p-6">
<div class="max-w-lg w-full text-center space-y-6">
<div class="inline-flex items-center justify-center size-14 rounded-xl bg-[#4F86C6]/20 border border-[#4F86C6]/40 text-[#4F86C6]">
<span class="material-symbols-outlined text-3xl">view_in_ar</span>
</div>
<h1 class="text-4xl md:text-5xl font-black tracking-tight">{name}</h1>
<p class="text-gray-400 text-lg">{tagline}</p>
<p class="text-[#4F86C6] text-sm font-bold uppercase tracking-wider">{genre}</p>
<div class="flex flex-col sm:flex-row gap-4 justify-center pt-4">
<a href="/worlds" class="inline-flex items-center justify-center gap-2 rounded-xl h-12 px-8 bg-[#4F86C6] hover:bg-[#7a0bb2] text-white text-base font-bold transition-colors">
<span class="material-symbols-outlined">arrow_back</span>
Back to Discover
</a>
</div>
<p class="text-gray-500 text-sm pt-8">Choose another world to re-enter from the discovery page.</p>
</div>
</body>
</html>"""


@app.route("/world/<slug>")
def world_entry(slug: str):
    """Enter a world by slug; page includes Back to Discover link to /worlds."""
    data = WORLD_DATA.get(slug)
    if not data:
        return f"<p>World '{slug}' not found. <a href='/worlds'>Back to Discover</a></p>", 404
    return _world_entry_html(
        name=data["name"],
        tagline=data["tagline"],
        genre=data["genre"],
    )


@app.route("/api/worlds", methods=["GET"])
def api_worlds():
    """Optional: list worlds for client-side use."""
    return jsonify({"worlds": list(WORLD_DATA.keys()), "data": WORLD_DATA})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = 5001
    print("")
    print("  Personalization API + World Discovery")
    print("  --------------------------------------")
    print(f"  Conversation:     http://127.0.0.1:{port}/")
    print(f"  World templates: http://127.0.0.1:{port}/worlds")
    print(f"  Enter a world:    http://127.0.0.1:{port}/world/<slug>")
    print("  --------------------------------------")
    print("")
    app.run(port=port, debug=True)
