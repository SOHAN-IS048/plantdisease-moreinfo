import streamlit as st
from pathlib import Path
from PIL import Image
import datetime
import io

# ------------------------------------
# CONFIG
# ------------------------------------
THUMB_SIZE = (260, 160)
THUMBS_SUB = "thumbs"
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

BASE = Path(__file__).parent.resolve()
IMAGES_DIR = BASE / "images"    # dataset folder
UPLOADS_DIR = BASE / "uploads"  # user uploads

# Create folders if missing
for folder in [IMAGES_DIR, UPLOADS_DIR]:
    folder.mkdir(exist_ok=True)
    (folder / THUMBS_SUB).mkdir(parents=True, exist_ok=True)

# ------------------------------------
# THUMBNAILS
# ------------------------------------
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
        print(f"Thumbnail error for {src}: {e}")

def ensure_thumb(folder: Path, filename: str) -> Path:
    src = folder / filename
    dest = thumb_path(folder, filename)
    if not dest.exists() and src.exists():
        make_thumbnail(src, dest)
    return dest if dest.exists() else src

def list_images(folder: Path):
    return sorted([p.name for p in folder.iterdir()
                   if p.suffix.lower() in ALLOWED_EXT and p.is_file()])

def read_bytes(path: Path) -> bytes:
    return path.read_bytes()

# ------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------
st.set_page_config(page_title="Agrimaster Dataset", layout="wide")
st.title("🌱 Agrimaster Dataset")

# ------------------------------------
# SEARCH BAR
# ------------------------------------
st.markdown("### 🔍 Search leaf disease by name")
search_query = st.text_input("Search", placeholder="Type disease name or file name...")

# ------------------------------------
# UPLOAD SECTION
# ------------------------------------
st.header("Upload images")

col_left, col_right = st.columns([2, 1])

with col_right:
    st.markdown("**Save uploaded files to:**")
    destination = st.radio("Destination folder", ("uploads", "dataset (images/)"))
    save_to_dataset = destination == "dataset (images/)"
    st.markdown("---")

with col_left:
    uploaded_files = st.file_uploader(
        "Select image files (multiple)", 
        accept_multiple_files=True,
        type=[ext.replace(".", "") for ext in ALLOWED_EXT],
    )
    if st.button("Upload selected"):
        if not uploaded_files:
            st.warning("No files selected.")
        else:
            saved = []
            folder = IMAGES_DIR if save_to_dataset else UPLOADS_DIR

            for up in uploaded_files:
                name = Path(up.name).name.replace(" ", "_")
                ext = Path(name).suffix.lower()
                if ext not in ALLOWED_EXT:
                    continue

                dest = folder / name
                if dest.exists():
                    stem = Path(name).stem
                    dest = folder / f"{stem}_{int(datetime.datetime.now().timestamp())}{ext}"

                with open(dest, "wb") as f:
                    f.write(up.getbuffer())

                make_thumbnail(dest, thumb_path(folder, dest.name))
                saved.append(dest.name)

            st.success(f"Uploaded {len(saved)} file(s).")
            st.session_state["last_uploaded"] = (str(folder), saved[-1])
            st.experimental_rerun()

st.markdown("---")

# ------------------------------------
# GALLERY GRID
# ------------------------------------
def show_grid(folder, images, prefix):
    cols = st.columns(4)

    for idx, name in enumerate(images):
        c = cols[idx % 4]
        thumb = ensure_thumb(folder, name)

        try:
            c.image(str(thumb), use_container_width=True)
        except:
            c.write("Preview error")

        c.caption(name)

        c.download_button(
            "Download",
            data=read_bytes(folder / name),
            file_name=name,
            mime="image/*",
            key=f"dl_{prefix}_{name}"
        )

# ------------------------------------
# FILTERING BY SEARCH QUERY
# ------------------------------------
dataset_images = list_images(IMAGES_DIR)
uploaded_images = list_images(UPLOADS_DIR)

if search_query:
    search_query = search_query.lower()
    dataset_images = [n for n in dataset_images if search_query in n.lower()]
    uploaded_images = [n for n in uploaded_images if search_query in n.lower()]

# ------------------------------------
# DATASET GALLERY
# ------------------------------------
st.subheader("Dataset images")

if dataset_images:
    show_grid(IMAGES_DIR, dataset_images, "ds")
else:
    st.info("No matching dataset images found.")

st.markdown("---")

# ------------------------------------
# UPLOADED GALLERY
# ------------------------------------
st.subheader("Uploaded images")

if uploaded_images:
    show_grid(UPLOADS_DIR, uploaded_images, "up")
else:
    st.info("No matching uploaded images found.")

# ------------------------------------
# LAST UPLOADED PREVIEW
# ------------------------------------
st.markdown("---")
st.header("Last uploaded")

if "last_uploaded" in st.session_state:
    folder_str, filename = st.session_state["last_uploaded"]
    path = Path(folder_str) / filename
    if path.exists():
        st.image(str(path), use_container_width=True)
        st.download_button("Download", data=read_bytes(path), file_name=filename)
    else:
        st.write("No recent uploads found.")
else:
    st.write("Upload a file to preview it here.")
