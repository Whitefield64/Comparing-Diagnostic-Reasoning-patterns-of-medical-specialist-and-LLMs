import json
import re
from pathlib import Path
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
CASES_DIR   = Path(__file__).parent.parent / "cases"
CONFIG_FILE = Path(__file__).parent / "config.json"


def normalize(raw: str) -> str:
    return re.sub(r"\.(md|txt)$", "", raw, flags=re.IGNORECASE).strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config")
def api_config():
    defaults = {"consensus_min_votes": 5, "consensus_min_agreement": 0.5}
    if CONFIG_FILE.exists():
        try:
            return jsonify(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return jsonify(defaults)


@app.route("/api/text")
def api_text():
    case_name = normalize(request.args.get("case", ""))
    for ext in (".md", ".txt"):
        f = CASES_DIR / f"{case_name}{ext}"
        if f.exists():
            return jsonify({"text": f.read_text(encoding="utf-8")})
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5002)
