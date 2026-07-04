import os
import streamlit as st
from PIL import Image
import zipfile
import tempfile
import shutil
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Duplicate Image Finder",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
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

def dhash(image, hash_size=8):
    """Generate perceptual hash for an image"""
    # Convert to grayscale and resize
    image = image.convert('L').resize((hash_size + 1, hash_size), Image.LANCZOS)
    
    # Calculate difference hash
    diff = []
    for y in range(hash_size):
        for x in range(hash_size):
            diff.append(image.getpixel((x, y)) > image.getpixel((x + 1, y)))
    
    return ''.join(['1' if v else '0' for v in diff])

def extract_zip(zip_file, extract_path):
    """Extract ZIP file to a temporary directory"""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return True
    except Exception as e:
        st.error(f"❌ Error extracting ZIP file: {e}")
        return False

def find_duplicate_images(folder_path, progress_bar, status_text):
    """Find duplicate images in a folder using perceptual hashing"""
    hashes = {}
    duplicates = []
    total_files = 0
    processed_files = 0
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
    
    # Count total image files
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                total_files += 1
    
    if total_files == 0:
        return duplicates, 0
    
    # Process files
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(root, file)
                processed_files += 1
                
                # Update progress
                progress_bar.progress(processed_files / total_files)
                status_text.text(f"Processing: {file} ({processed_files}/{total_files})")
                
                try:
                    with Image.open(file_path) as img:
                        img_hash = dhash(img)
                        
                        if img_hash in hashes:
                            duplicates.append((file_path, hashes[img_hash]))
                        else:
                            hashes[img_hash] = file_path
                            
                except Exception as e:
                    st.warning(f"⚠️ Could not process {file}: {str(e)}")
                    continue
    
    return duplicates, total_files

def get_image_size(file_path):
    """Get file size in human-readable format"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

def display_image(file_path):
    """Display image with error handling"""
    try:
        img = Image.open(file_path)
        # Resize for display if too large
        img.thumbnail((400, 400), Image.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def get_relative_path(full_path, base_path):
    """Get relative path from base path"""
    try:
        return os.path.relpath(full_path, base_path)
    except:
        return os.path.basename(full_path)

# Main App
def main():
    # Header
    st.markdown("<h1>🔍 Duplicate Image Finder</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Upload a ZIP file containing images to find duplicates</p>", unsafe_allow_html=True)
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📖 Instructions")
        st.markdown("""
        ### How to use:
        1. **Create a ZIP file** containing your images
        2. **Upload the ZIP** using the file uploader
        3. **Click 'Start Scanning'** to find duplicates
        4. **Review results** and manage duplicates
        
        ---
        
        ### 💡 Tips:
        - ZIP can contain nested folders
        - All image files will be scanned
        - Duplicates are found using perceptual hashing
        """)
        
        st.markdown("---")
        st.markdown("### 📋 About")
        st.info("""
        This tool uses **perceptual hashing** to find duplicate images, even if they have been:
        - Resized
        - Slightly edited
        - Saved in different formats
        
        **Supported formats:** PNG, JPG, JPEG, BMP, GIF, WEBP
        """)
    
    # File uploader
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📦 Upload ZIP File Containing Images",
        type=['zip'],
        help="Upload a ZIP file containing images you want to scan for duplicates"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Main content area
    if uploaded_file is not None:
        # Display file info
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # Convert to MB
        st.info(f"📁 **Uploaded:** {uploaded_file.name} ({file_size:.2f} MB)")
        
        if st.button("🚀 Start Scanning", use_container_width=True):
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Extract ZIP file
                with st.spinner("📦 Extracting ZIP file..."):
                    extract_success = extract_zip(uploaded_file, temp_dir)
                
                if not extract_success:
                    shutil.rmtree(temp_dir)
                    return
                
                st.success("✅ ZIP file extracted successfully!")
                
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("🔎 Scanning for duplicates..."):
                    duplicates, total_files = find_duplicate_images(temp_dir, progress_bar, status_text)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.success("✅ Scan Complete!")
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class='stats-box'>
                        <p class='stats-number'>{total_files}</p>
                        <p class='stats-label'>Images Scanned</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class='stats-box'>
                        <p class='stats-number'>{len(duplicates)}</p>
                        <p class='stats-label'>Duplicates Found</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    unique_images = total_files - len(duplicates)
                    st.markdown(f"""
                    <div class='stats-box'>
                        <p class='stats-number'>{unique_images}</p>
                        <p class='stats-label'>Unique Images</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Store results in session state
                if 'duplicates' not in st.session_state:
                    st.session_state.duplicates = []
                st.session_state.duplicates = duplicates
                st.session_state.temp_dir = temp_dir
                
                # Display duplicates
                if duplicates:
                    st.header("🔁 Duplicate Images Found")
                    st.markdown(f"*Found {len(duplicates)} duplicate image(s)*")
                    
                    for idx, (duplicate_path, original_path) in enumerate(duplicates, 1):
                        with st.expander(f"**Duplicate Set #{idx}**", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("##### 📄 Original")
                                img1 = display_image(original_path)
                                if img1:
                                    st.image(img1, use_container_width=True)
                                st.text(f"📍 {os.path.basename(original_path)}")
                                st.text(f"📂 {get_relative_path(original_path, temp_dir)}")
                                st.text(f"💾 {get_image_size(original_path)}")
                            
                            with col2:
                                st.markdown("##### 🔁 Duplicate")
                                img2 = display_image(duplicate_path)
                                if img2:
                                    st.image(img2, use_container_width=True)
                                st.text(f"📍 {os.path.basename(duplicate_path)}")
                                st.text(f"📂 {get_relative_path(duplicate_path, temp_dir)}")
                                st.text(f"💾 {get_image_size(duplicate_path)}")
                            
                            st.markdown("---")
                            st.info("💡 **Tip:** These images are similar based on perceptual hashing. Review them to confirm they are truly duplicates.")
                else:
                    st.success("🎉 No duplicates found! All images are unique.")
                    st.balloons()
                
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
            finally:
                # Note: We keep temp_dir for viewing images, but it will be cleaned up when session ends
                pass
    else:
        # Welcome screen
        st.markdown("""
        <div style='text-align: center; padding: 3rem;'>
            <h2>👆 Upload a ZIP file to get started</h2>
            <p style='font-size: 1.2rem; color: #666; margin-top: 1rem;'>
                The tool will scan all images in the ZIP file and find duplicates
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### ⚡ Fast Scanning
            Uses efficient perceptual hashing algorithm
            """)
        
        with col2:
            st.markdown("""
            ### 🎯 Accurate Detection
            Finds duplicates even after resizing or editing
            """)
        
        with col3:
            st.markdown("""
            ### 🖼️ Visual Comparison
            Side-by-side view of original and duplicate
            """)
        
        # Example section
        st.markdown("---")
        st.markdown("### 📦 How to prepare your ZIP file")
        st.markdown("""
        1. Select all the images you want to check
        2. Right-click and choose "Send to" → "Compressed (zipped) folder" (Windows)
        3. Or use any ZIP compression tool
        4. Upload the created ZIP file here
        
        The ZIP can contain:
        - Images in the root folder
        - Images in nested subfolders
        - Mix of different image formats
        """)

if __name__ == "__main__":
    main()