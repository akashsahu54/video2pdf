import streamlit as st
import subprocess
import os
import shutil
import re
import glob
from PIL import Image
from fpdf import FPDF

# Session state setup
if 'download_complete' not in st.session_state:
    st.session_state.download_complete = False
if 'thumbs_path' not in st.session_state:
    st.session_state.thumbs_path = []
if 'selected_thumbs' not in st.session_state:
    st.session_state.selected_thumbs = []
if 'current_video_url' not in st.session_state:
    st.session_state.current_video_url = ''
if 'thumbnail_mode' not in st.session_state:
    st.session_state.thumbnail_mode = 'Automatic'
if 'video_title' not in st.session_state:
    st.session_state.video_title = ''

st.title("📸 YT SnapPDF")

# YouTube URL input
video_url = st.text_input("Enter YouTube video URL:", key="video_url_input")

# Reset state if URL changes
if video_url != st.session_state.current_video_url:
    # Clear thumbs folder
    if os.path.exists("thumbs"):
        shutil.rmtree("thumbs")
    os.makedirs("thumbs", exist_ok=True)
    # Clear all .mp4 and .pdf files
    for file in glob.glob("*.mp4"):
        os.remove(file)
    for file in glob.glob("*.pdf"):
        os.remove(file)
    # Reset session state
    st.session_state.download_complete = False
    st.session_state.thumbs_path = []
    st.session_state.selected_thumbs = []
    st.session_state.current_video_url = video_url
    st.session_state.video_title = ''
    # Force rerun to ensure clean state
    st.rerun()

# Ask user for thumbnail mode
previous_mode = st.session_state.thumbnail_mode
st.session_state.thumbnail_mode = st.radio(
    "How do you want to extract thumbnails?",
    ("Automatic", "Manual"),
    help="Automatic: Extracts thumbnails every 30 seconds. Manual: Specify timestamps in MM:SS format, e.g., 5:40, 10:22."
)

# Reset state if mode changes
if previous_mode != st.session_state.thumbnail_mode:
    st.session_state.download_complete = False
    st.session_state.thumbs_path = []
    st.session_state.selected_thumbs = []

# Manual mode timestamp input
manual_timestamps = []
if st.session_state.thumbnail_mode == "Manual":
    timestamps_input = st.text_input(
        "Enter timestamps (MM:SS format, comma-separated, e.g., 5:40, 10:22):",
        placeholder="5:40, 10:22, 15:00"
    )
    if timestamps_input:
        try:
            # Convert MM:SS to seconds
            for ts in timestamps_input.split(","):
                ts = ts.strip()
                if ":" not in ts:
                    raise ValueError("Invalid format! Use MM:SS.")
                minutes, seconds = map(int, ts.split(":"))
                if minutes < 0 or seconds < 0 or seconds >= 60:
                    raise ValueError("Invalid minutes or seconds.")
                total_seconds = minutes * 60 + seconds
                manual_timestamps.append(total_seconds)
        except ValueError as e:
            st.error(f"❌ Error in timestamps: {e}")
            st.stop()

# Number of thumbnails per PDF page
thumbs_per_page = st.slider("Number of thumbnails per PDF page (recommended 6):", 2, 12, 6)

# Download video and generate thumbnails
if st.button("Download Video & Generate Thumbnails"):
    if video_url:
        # Clear thumbs folder
        if os.path.exists("thumbs"):
            shutil.rmtree("thumbs")
        os.makedirs("thumbs", exist_ok=True)
        # Clear all .mp4 and .pdf files
        for file in glob.glob("*.mp4"):
            os.remove(file)
        for file in glob.glob("*.pdf"):
            os.remove(file)
        
        # Get video title using yt-dlp
        try:
            result = subprocess.run(
                ["yt-dlp", "--get-title", video_url],
                capture_output=True, text=True, check=True
            )
            video_title = result.stdout.strip()
            # Sanitize title to make it a valid filename
            video_title = re.sub(r'[^\w\s-]', '', video_title).replace(' ', '_')
            if not video_title:
                video_title = "video"  # Fallback title
            st.session_state.video_title = video_title
        except Exception as e:
            st.error(f"❌ Error fetching video title: {e}")
            video_title = "video"
            st.session_state.video_title = video_title

        # Download video with title as filename
        video_file = f"{video_title}.mp4"
        try:
            st.info("📥 Downloading video...")
            subprocess.run(
                ["yt-dlp", "-f", "mp4", "-o", video_file, video_url],
                check=True
            )
            st.success("✅ Video downloaded successfully!")
        except Exception as e:
            st.error(f"❌ Error downloading video: {e}")
            st.stop()

        # Re-encode video to ensure compatibility
        reencoded_file = f"reencoded_{video_title}.mp4"
        try:
            st.info("🔄 Re-encoding video for compatibility...")
            subprocess.run(
                ["ffmpeg", "-y", "-i", video_file, "-c:v", "libx264", "-c:a", "aac", reencoded_file],
                check=True
            )
            st.success("✅ Video re-encoded successfully!")
            # Update video_file to use re-encoded file
            video_file = reencoded_file
        except Exception as e:
            st.error(f"❌ Error re-encoding video: {e}")
            st.stop()

        st.info("🖼️ Generating thumbnails...")
        if st.session_state.thumbnail_mode == "Automatic":
            # Automatic: Every 30 seconds
            os.system(f"ffmpeg -y -i {video_file} -vf fps=1/30 thumbs/thumb_%03d.jpg")
            thumbs = sorted([f for f in os.listdir("thumbs") if f.endswith(".jpg")])
            st.session_state.thumbs_path = [os.path.join("thumbs", t) for t in thumbs]
            st.session_state.download_complete = True
            st.session_state.selected_thumbs = []
        else:
            # Manual: At specified timestamps
            if not manual_timestamps:
                st.error("Please enter valid timestamps for manual mode.")
                st.stop()
            thumbs = []
            for i, timestamp in enumerate(manual_timestamps):
                output_file = f"thumbs/thumb_{i:03d}.jpg"
                os.system(f"ffmpeg -y -i {video_file} -ss {timestamp} -vframes 1 {output_file}")
                if os.path.exists(output_file):
                    thumbs.append(output_file)
            st.session_state.thumbs_path = thumbs
            st.session_state.download_complete = True
            st.session_state.selected_thumbs = []
        
        if not st.session_state.thumbs_path:
            st.error("No thumbnails generated. Check timestamps or video.")
            st.stop()
    else:
        st.warning("Please enter a valid YouTube URL.")

# Display thumbnails
if st.session_state.download_complete and st.session_state.thumbs_path and st.session_state.current_video_url == video_url:
    st.write("### Thumbnails:")
    cols = st.columns(2)
    
    for i, thumb in enumerate(st.session_state.thumbs_path):
        with cols[i % 2]:
            # Set caption based on mode
            if st.session_state.thumbnail_mode == "Automatic":
                caption = f"{i*30} sec"
            else:
                if i < len(manual_timestamps):
                    seconds = manual_timestamps[i]
                    caption = f"{seconds // 60}:{seconds % 60:02d}"
                else:
                    caption = "Unknown"
            st.image(thumb, caption=caption)
            if st.button(f"Add to PDF - {caption}", key=f"btn_{i}"):
                if (thumb, caption) not in st.session_state.selected_thumbs:
                    st.session_state.selected_thumbs.append((thumb, caption))
                    st.rerun()

    # Show selected thumbnails
    if st.session_state.selected_thumbs:
        st.write("Selected for PDF:")
        for thumb in st.session_state.selected_thumbs:
            st.write(f"- {thumb[1]}")

        # Generate PDF
        if st.button("📄 Generate PDF"):
            # Clear existing PDFs before generating a new one
            for file in glob.glob("*.pdf"):
                os.remove(file)
            
            pdf = FPDF()
            
            # Add thumbnails to PDF pages
            for page_num in range(0, len(st.session_state.selected_thumbs), thumbs_per_page):
                pdf.add_page()
                pdf.set_font("Arial", "B", size=14)
                # Add video title at the top
                pdf.cell(0, 10, st.session_state.video_title, ln=True, align="C")
                pdf.set_font("Arial", size=12)
                pdf.ln(10)  # Add some space after title
                
                page_thumbs = st.session_state.selected_thumbs[page_num:page_num+thumbs_per_page]
                for i, (img_path, caption) in enumerate(page_thumbs):
                    x = 10 + (i % 2) * 100
                    y = 30 + (i // 2) * 100  # Adjusted y to account for title
                    pdf.text(x, y-5, caption)
                    pdf.image(img_path, x=x, y=y, w=90, h=60)
            
            pdf_file = f"{st.session_state.video_title}_thumbnails.pdf"
            pdf.output(pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button(f"⬇️ Download PDF", f, pdf_file)