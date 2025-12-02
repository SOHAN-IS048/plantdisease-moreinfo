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
# TRANSLATIONS (English + Kannada)
# ------------------------------------
TEXTS = {
    "English": {
        "page_title": "🌱 Agrimaster Dataset",
        "search_header": "🔍 Search leaf disease by name",
        "search_placeholder": "Type disease name or file name...",
        "upload_header": "Upload images",
        "save_to": "**Save uploaded files to:**",
        "destination_label": "Destination folder",
        "dest_uploads": "uploads",
        "dest_dataset": "dataset (images/)",
        "upload_button": "Upload selected",
        "no_files_selected": "No files selected.",
        "uploaded_success": "Uploaded {} file(s).",
        "dataset_images": "Dataset images",
        "no_dataset_matches": "No matching dataset images found.",
        "uploaded_images": "Uploaded images",
        "no_uploaded_matches": "No matching uploaded images found.",
        "last_uploaded": "Last uploaded",
        "download": "Download",
        "preview_error": "Preview error",
        "no_recent_uploads": "No recent uploads found.",
        "upload_label": "Select image files (multiple)",
    },
    "Kannada": {
        "page_title": "🌱 ಅಗ್ರಿಮಾಸ್ಟರ್ ಡೇಟಾಸೆಟ್",
        "search_header": "🔍 ಎಲೆ ರೋಗವನ್ನು ಹೆಸರಿನಿಂದ ಹುಡುಕಿ",
        "search_placeholder": "ರೋಗದ ಹೆಸರು ಅಥವಾ ಫೈಲ್ ಹೆಸರು ಟೈಪ್ ಮಾಡಿ...",
        "upload_header": "ಚಿತ್ರಗಳನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        "save_to": "**ಅಪ್ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳನ್ನು ಇಲ್ಲಿ ಉಳಿಸಿ:**",
        "destination_label": "ಗಮ್ಯ ಫೋಲ್ಡರ್",
        "dest_uploads": "ಅಪ್‌ಲೋಡ್‌ಗಳು",
        "dest_dataset": "ಡೇಟಾಸೆಟ್ (ಚಿತ್ರಗಳು/)",
        "upload_button": "ಆಯ್ದ ಫೈಲ್‌ಗಳನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        "no_files_selected": "ಯಾವುದೇ ಫೈಲ್ ಆಯ್ಕೆ ಮಾಡಿಲ್ಲ.",
        "uploaded_success": "{} ಫೈಲ್(ಗಳು) ಅಪ್ಲೋಡ್ ಆಗಿವೆ.",
        "dataset_images": "ಡೇಟಾಸೆಟ್ ಚಿತ್ರಗಳು",
        "no_dataset_matches": "ಹೊಂದಿಕೆಯಾಗುವ ಡೇಟಾಸೆಟ್ ಚಿತ್ರಗಳು ಕಂಡುಬರಲಿಲ್ಲ.",
        "uploaded_images": "ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರಗಳು",
        "no_uploaded_matches": "ಹೊಂದಿಕೆಯಾಗುವ ಅಪ್ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರಗಳು ಕಂಡುಬರಲಿಲ್ಲ.",
        "last_uploaded": "ಕೊನೆಯದಾಗಿ ಅಪ್ಲೋಡ್ ಮಾಡಲಾದವು",
        "download": "ಡೌನ್‌ಲೋಡ್",
        "preview_error": "ಪ್ರಿವ್ಯೂ ದೋಷ",
        "no_recent_uploads": "ಇತ್ತೀಚೆಗೆ ಅಪ್ಲೋಡ್ ಮಾಡಿರೋದಿಲ್ಲ.",
        "upload_label": "ಚಿತ್ರ ಫೈಲ್‌ಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಿ (ಬಹು ಫೈಲ್‌ಗಳು)",
    }
}

def T(lang: str, key: str, *fmt_args):
    txt = TEXTS.get(lang, TEXTS["English"]).get(key, "")
    if fmt_args:
        try:
            return txt.format(*fmt_args)
        except Exception:
            return txt
    return txt

# ------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

# Language selector in the sidebar so student can switch
lang_choice = st.sidebar.selectbox("Language / ಭಾಷೆ", ["English", "Kannada"],
                                   index=0 if st.session_state["lang"]=="English" else 1)
st.session_state["lang"] = lang_choice
lang = st.session_state["lang"]

st.set_page_config(page_title=T(lang, "page_title"), layout="wide")
st.title(T(lang, "page_title"))

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
# SEARCH BAR
# ------------------------------------
st.markdown(f"### {T(lang, 'search_header')}")
search_query = st.text_input(T(lang, "search_header"), placeholder=T(lang, "search_placeholder"))

# ------------------------------------
# UPLOAD SECTION
# ------------------------------------
st.header(T(lang, "upload_header"))

col_left, col_right = st.columns([2, 1])

with col_right:
    st.markdown(T(lang, "save_to"), unsafe_allow_html=True)
    destination = st.radio(T(lang, "destination_label"),
                          (T(lang, "dest_uploads"), T(lang, "dest_dataset")))
    save_to_dataset = (destination == T(lang, "dest_dataset"))
    st.markdown("---")

with col_left:
    uploaded_files = st.file_uploader(
        T(lang, "upload_label"),
        accept_multiple_files=True,
        type=[ext.replace(".", "") for ext in ALLOWED_EXT],
    )

    if st.button(T(lang, "upload_button")):
        if not uploaded_files:
            st.warning(T(lang, "no_files_selected"))
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

            st.success(T(lang, "uploaded_success").format(len(saved)))
            st.session_state["last_uploaded"] = (str(folder), saved[-1])
            st.experimental_rerun()

st.markdown("---")

# ------------------------------------
# GALLERY GRID
# ------------------------------------
def show_grid(folder: Path, images, prefix: str):
    # keep original 4-column layout
    cols = st.columns(4)

    for idx, name in enumerate(images):
        c = cols[idx % 4]
        thumb = ensure_thumb(folder, name)

        try:
            c.image(str(thumb), use_container_width=True)
        except:
            c.write(T(lang, "preview_error"))

        c.caption(name)

        c.download_button(
            T(lang, "download"),
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
    sq = search_query.lower()
    dataset_images = [n for n in dataset_images if sq in n.lower()]
    uploaded_images = [n for n in uploaded_images if sq in n.lower()]

# ------------------------------------
# DATASET GALLERY
# ------------------------------------
st.subheader(T(lang, "dataset_images"))

if dataset_images:
    show_grid(IMAGES_DIR, dataset_images, "ds")
else:
    st.info(T(lang, "no_dataset_matches"))

st.markdown("---")

# ------------------------------------
# UPLOADED GALLERY
# ------------------------------------
st.subheader(T(lang, "uploaded_images"))

if uploaded_images:
    show_grid(UPLOADS_DIR, uploaded_images, "up")
else:
    st.info(T(lang, "no_uploaded_matches"))

# ------------------------------------
# LAST UPLOADED PREVIEW
# ------------------------------------
st.markdown("---")
st.header(T(lang, "last_uploaded"))

if "last_uploaded" in st.session_state:
    folder_str, filename = st.session_state["last_uploaded"]
    path = Path(folder_str) / filename
    if path.exists():
        st.image(str(path), use_container_width=True)
        st.download_button(T(lang, "download"), data=read_bytes(path), file_name=filename)
    else:
        st.write(T(lang, "no_recent_uploads"))
else:
    st.write(T(lang, "no_recent_uploads"))
