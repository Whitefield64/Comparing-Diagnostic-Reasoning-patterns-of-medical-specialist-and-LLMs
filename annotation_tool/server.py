import os
from pathlib import Path
from flask import Flask, render_template, jsonify, abort

app = Flask(__name__)

CASES_DIR = Path(__file__).parent.parent / "cases"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/cases")
def list_cases():
    files = sorted(f.name for f in CASES_DIR.glob("*.md"))
    return jsonify(files)


@app.route("/api/cases/<path:filename>")
def get_case(filename):
    path = CASES_DIR / filename
    if not path.exists() or not path.suffix == ".md":
        abort(404)
    return app.response_class(
        response=path.read_text(encoding="utf-8"),
        mimetype="text/plain",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
