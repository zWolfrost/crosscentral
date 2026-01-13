import os
from flask import Flask, Response, render_template
from werkzeug.utils import safe_join
import mimetypes

BASE_DIR = os.path.abspath("share")

if not os.path.exists(BASE_DIR):
	os.makedirs(BASE_DIR)

app = Flask(__name__, static_folder="static", template_folder="static")

def get_dir_entries(rel_path):
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

	return entries

def render_directory(rel_path, error=None):
	return render_template(
		"directory.j2",
		entries=get_dir_entries(rel_path) if not error else [],
		path=rel_path,
		path_parent=os.path.dirname(rel_path),
		error=error
	)

def file_stream(filepath):
	with open(filepath, "rb") as f:
		while chunk := f.read(1024*1024):
			yield chunk

@app.route("/", defaults={"rel_path": ""})
@app.route("/<path:rel_path>")
def browse(rel_path):
	full_path = safe_join(BASE_DIR, rel_path)

	if not full_path or os.path.commonpath([BASE_DIR, full_path]) != BASE_DIR:
		return render_directory(rel_path, error="Nice try.")

	if not os.path.exists(full_path):
		return render_directory(rel_path, error="This directory does not exist."), 404

	if os.path.isdir(full_path):
		if not os.listdir(full_path):
			return render_directory(rel_path, error="This directory is empty.")
		return render_directory(rel_path)
	elif os.path.isfile(full_path):
		mime_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
		return Response(file_stream(full_path), headers={ "Content-Type": mime_type })
	else:
		return render_directory(rel_path, error="This file is broken."), 400

if __name__ == "__main__":
	app.run(debug=True, extra_files=["./static/directory.j2", "./static/style.css"])
