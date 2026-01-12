import os
from flask import Flask, send_from_directory, abort, render_template_string
from werkzeug.utils import safe_join

BASE_DIR = os.path.abspath("share")

if not os.path.exists(BASE_DIR):
	os.makedirs(BASE_DIR)

with open("./static/directory.j2") as f:
   DIRECTORY_TEMPLATE = f.read()

app = Flask(__name__, static_folder="./static")

def list_directory(rel_path):
	full_path = safe_join(BASE_DIR, rel_path)

	entries = []
	for item in os.listdir(full_path):
		entries.append({
			"filename": item,
			"extension": item.split('.')[-1] if '.' in item else '',
			"filepath": os.path.join(rel_path, item),
			"is_dir": os.path.isdir(os.path.join(full_path, item))
		})
	entries = sorted(entries, key=lambda e: (not e["is_dir"], e["filename"].lower()))

	return render_template_string(
		DIRECTORY_TEMPLATE,
		entries=entries,
		path=rel_path,
		path_parent=os.path.dirname(rel_path)
	)

@app.route("/", defaults={"rel_path": ""})
@app.route("/<path:rel_path>")
def browse(rel_path):
	if "../" in rel_path:
		return "Nice try. Asshole.", 403

	full_path = safe_join(BASE_DIR, rel_path)

	if full_path and os.path.exists(full_path):
		if os.path.isdir(full_path):
			return list_directory(rel_path)
		elif os.path.isfile(full_path):
			return send_from_directory(BASE_DIR, rel_path, as_attachment=False)

	abort(404)

if __name__ == "__main__":
	app.run(debug=True, extra_files=["./static/directory.j2", "./static/style.css"])
