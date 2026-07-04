import os
import streamlit as st
from PIL import Image
import zipfile
import tempfile
import shutil
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(page_title="Duplicate Image Finder", page_icon="🔍", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .duplicate-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stats-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin: 1rem 0;
    }
    .stats-number {
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
    }
    .stats-label {
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .upload-box {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 3rem;
        text-align: center;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        margin: 2rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def dhash(image, hash_size=8):
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.LANCZOS)
    diff = [image.getpixel((x, y)) > image.getpixel((x + 1, y)) for y in range(hash_size) for x in range(hash_size)]
    return ''.join(['1' if v else '0' for v in diff])

def extract_zip(zip_file, extract_path):
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True
    except Exception as e:
        st.error(f"❌ Error extracting ZIP file: {e}")
        return False

def find_duplicate_images(folder_path, progress_bar, status_text):
    hashes, duplicates = {}, []
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
    files = [os.path.join(root, f) for root, _, fs in os.walk(folder_path) for f in fs if f.lower().endswith(image_extensions)]
    total = len(files)
    for i, path in enumerate(files, 1):
        progress_bar.progress(i / total)
        status_text.text(f"Processing {os.path.basename(path)} ({i}/{total})")
        try:
            with Image.open(path) as img:
                img_hash = dhash(img)
                if img_hash in hashes:
                    duplicates.append((path, hashes[img_hash]))
                else:
                    hashes[img_hash] = path
        except Exception as e:
            st.warning(f"⚠️ Could not process {os.path.basename(path)}: {e}")
    return duplicates, total

def get_image_size(path):
    size = os.path.getsize(path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def display_image(path):
    try:
        img = Image.open(path)
        img.thumbnail((400, 400))
        return img
    except:
        return None

# --- Main App ---
def main():
    st.markdown("<h1>🔍 Duplicate Image Finder</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Upload images (ZIP or multiple) to find duplicates</p>", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📖 Instructions")
        st.markdown("""
        1. Upload a **ZIP file** or **multiple images**
        2. Click **Start Scanning**
        3. View duplicate results
        """)
        st.info("Uses **perceptual hashing** to detect duplicates, even after resizing or minor edits.")

    # --- Upload Section ---
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)

    upload_choice = st.radio(
        "Choose upload method:",
        ("📦 Upload ZIP File", "🖼️ Upload Multiple Images"),
        horizontal=True
    )

    temp_dir = tempfile.mkdtemp()
    uploaded_files = []

    if upload_choice == "📦 Upload ZIP File":
        uploaded_zip = st.file_uploader("Upload ZIP File Containing Images", type=['zip'], help="Upload a ZIP file containing images")
        if uploaded_zip:
            with st.spinner("📦 Extracting ZIP file..."):
                extract_success = extract_zip(uploaded_zip, temp_dir)
            if extract_success:
                st.success("✅ ZIP file extracted successfully!")
                uploaded_files = list(Path(temp_dir).rglob("*.*"))
            else:
                st.stop()

    elif upload_choice == "🖼️ Upload Multiple Images":
        uploaded_images = st.file_uploader(
            "Drag and drop multiple image files",
            type=["png", "jpg", "jpeg", "bmp", "gif", "webp"],
            accept_multiple_files=True
        )

        if uploaded_images:
            for file in uploaded_images:
                file_path = os.path.join(temp_dir, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
            st.success(f"✅ {len(uploaded_images)} image(s) uploaded successfully!")
            uploaded_files = [os.path.join(temp_dir, file.name) for file in uploaded_images]

    st.markdown("</div>", unsafe_allow_html=True)

    # --- Start Scanning ---
    if uploaded_files:
        if st.button("🚀 Start Scanning", use_container_width=True):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()

                with st.spinner("🔎 Scanning for duplicates..."):
                    duplicates, total_files = find_duplicate_images(temp_dir, progress_bar, status_text)

                progress_bar.empty()
                status_text.empty()

                st.success("✅ Scan Complete!")

                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div class='stats-box'><p class='stats-number'>{total_files}</p><p class='stats-label'>Images Scanned</p></div>", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div class='stats-box'><p class='stats-number'>{len(duplicates)}</p><p class='stats-label'>Duplicates Found</p></div>", unsafe_allow_html=True)
                with col3:
                    unique_images = total_files - len(duplicates)
                    st.markdown(f"<div class='stats-box'><p class='stats-number'>{unique_images}</p><p class='stats-label'>Unique Images</p></div>", unsafe_allow_html=True)

                st.markdown("---")

                if duplicates:
                    st.header("🔁 Duplicate Images Found")
                    for idx, (dup, orig) in enumerate(duplicates, 1):
                        with st.expander(f"**Duplicate Set #{idx}**", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("##### 📄 Original")
                                img1 = display_image(orig)
                                if img1:
                                    st.image(img1, use_container_width=True)
                                st.text(f"📍 {os.path.basename(orig)}")
                                st.text(f"💾 {get_image_size(orig)}")

                            with col2:
                                st.markdown("##### 🔁 Duplicate")
                                img2 = display_image(dup)
                                if img2:
                                    st.image(img2, use_container_width=True)
                                st.text(f"📍 {os.path.basename(dup)}")
                                st.text(f"💾 {get_image_size(dup)}")
                else:
                    st.success("🎉 No duplicates found! All images are unique.")
                    st.balloons()

            except Exception as e:
                st.error(f"❌ Error: {e}")

    else:
        st.markdown("""
        <div style='text-align: center; padding: 3rem;'>
            <h2>👆 Upload a ZIP file or multiple images to get started</h2>
            <p style='font-size: 1.2rem; color: #666; margin-top: 1rem;'>
                The tool will scan all images and find duplicates.
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
