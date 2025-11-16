from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from pathlib import Path
import datetime
import werkzeug.utils
from PIL import Image

THUMB_SIZE = (260, 160)   # width x height for cards (adjust if you like)
THUMBS_SUB = "thumbs"

def thumb_path(folder: Path, filename: str) -> Path:
    return folder / THUMBS_SUB / (Path(filename).stem + ".jpg")

def make_thumbnail(src: Path, dest: Path, size=THUMB_SIZE):
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail(size, Image.LANCZOS)
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, format="JPEG", quality=80)
    except Exception as e:
        print("Thumb error:", e)

BASE = Path(__file__).parent.resolve()
IMAGES_DIR = BASE / "images"
UPLOADS_DIR = BASE / "uploads"
TEMPLATES_DIR = BASE / "templates"

IMAGES_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# ensure thumbs directories exist
(IMAGES_DIR / THUMBS_SUB).mkdir(exist_ok=True)
(UPLOADS_DIR / THUMBS_SUB).mkdir(exist_ok=True)

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(BASE / "static"))

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

def list_image_files(folder: Path):
    return sorted([p.name for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT and p.is_file()])

@app.route("/")
def index():
    dataset_images = list_image_files(IMAGES_DIR)
    uploaded_images = list_image_files(UPLOADS_DIR)
    return render_template("gallery.html", dataset_images=dataset_images, uploaded_images=uploaded_images)

@app.route("/images/<path:filename>")
def serve_image(filename):
    p = IMAGES_DIR / filename
    if p.exists():
        return send_from_directory(str(IMAGES_DIR), filename)
    p2 = UPLOADS_DIR / filename
    if p2.exists():
        return send_from_directory(str(UPLOADS_DIR), filename)
    return ("Not found", 404)

@app.route("/thumbs/<which>/<path:filename>")
def serve_thumb(which, filename):
    if which not in ("images", "uploads"):
        return ("Not found", 404)

    folder = IMAGES_DIR if which == "images" else UPLOADS_DIR
    src = folder / filename
    if not src.exists():
        return ("Not found", 404)

    dest = thumb_path(folder, filename)
    if not dest.exists():
        try:
            make_thumbnail(src, dest)
        except Exception:
            return send_from_directory(str(folder), filename)

    return send_file(str(dest), mimetype="image/jpeg", conditional=True)

@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    saved = []
    for f in files:
        if not f:
            continue
        fname = werkzeug.utils.secure_filename(f.filename)
        ext = Path(fname).suffix.lower()
        if ext not in ALLOWED_EXT:
            continue
        dest = UPLOADS_DIR / fname
        if dest.exists():
            stem = Path(fname).stem
            dest = UPLOADS_DIR / f"{stem}_{int(datetime.datetime.now().timestamp())}{ext}"
        f.save(dest)
        saved.append(dest.name)
        # create thumbnail right away
        try:
            make_thumbnail(dest, thumb_path(UPLOADS_DIR, dest.name))
        except Exception as e:
            print("Failed to create thumbnail for uploaded file:", e)
    return jsonify({"saved": saved})

if __name__ == "__main__":
    # disable reloader to avoid "signal only works in main thread" in some IDEs
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
