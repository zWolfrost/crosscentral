import os
from flask import Flask, Response, request, render_template
from werkzeug.utils import safe_join
import mimetypes

BASE_DIR = os.path.abspath("/srv/share")

app = Flask(__name__, static_folder="static", template_folder="static")

def guess_mimetype(filepath):
	return mimetypes.guess_type(filepath)[0] or "application/octet-stream"

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

def render_file(rel_path, error=None):
	SUPPORTED_PREVIEWS = [
		"image/png", "image/jpeg", "image/gif", "image/bmp", "image/webp",
		"video/mp4", "video/webm",
		"audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg", "audio/flac", "audio/x-flac"
	]

	mimetype = guess_mimetype(rel_path)

	return render_template(
		"file.j2",
		filename=os.path.basename(rel_path),
		mimetype=mimetype,
		preview=(mimetype in SUPPORTED_PREVIEWS),
		path=rel_path,
		path_parent=os.path.dirname(rel_path),
		error=error
	)

def send_file_nginx(rel_path,  as_attachment=False):
	NGINX_PREFIX = "_protected"

	response = Response()
	response.headers["X-Accel-Redirect"] = f"/{NGINX_PREFIX}/{rel_path}"
	response.headers["Content-Type"] = guess_mimetype(safe_join(BASE_DIR, rel_path))

	if as_attachment:
		response.headers["Content-Disposition"] = f'attachment; filename="{os.path.basename(rel_path)}"'

	return response

@app.route("/", defaults={"rel_path": ""})
@app.route("/<path:rel_path>")
def browse(rel_path):
	full_path = safe_join(BASE_DIR, rel_path)

	if not full_path or os.path.commonpath([BASE_DIR, full_path]) != BASE_DIR:
		return render_directory(rel_path, error="Nice try.")

	if not os.path.exists(full_path):
		return render_directory(rel_path, error="This file/directory does not exist."), 404

	if os.path.isdir(full_path):
		if not os.listdir(full_path):
			return render_directory(rel_path, error="This directory is empty.")
		return render_directory(rel_path)
	elif os.path.isfile(full_path):
		inline = request.args.get("inline") == "1"
		download = request.args.get("download") == "1"
		if inline or download:
			return send_file_nginx(rel_path, as_attachment=download)
		else:
			return render_file(rel_path)
	else:
		return render_directory(rel_path, error="This file is broken."), 400

if __name__ == "__main__":
	app.run("127.0.0.1", 5000, debug=True, extra_files=["./static/directory.j2", "./static/file.j2", "./static/style.css"])
