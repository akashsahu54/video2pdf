import streamlit as st
import subprocess
import os
import shutil
import re
import glob
import stat
import requests
from PIL import Image
from fpdf import FPDF
from urllib.parse import urlparse, parse_qs

# Set your YouTube Data API key
YOUTUBE_API_KEY = "AIzaSyBqnLbn8m8hmbOorgc2rGFfOaYl7BCfZz4"

# Safely remove folders (with permission handling)
def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    if os.path.exists(path):
        shutil.rmtree(path, onerror=on_rm_error)

# Extract video ID from YouTube URL
def extract_video_id(url):
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path[1:]
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        query = parse_qs(parsed_url.query)
        return query.get("v", [None])[0]
    return None

# Get video title using YouTube Data API
def fetch_video_title(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        return None
    api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(api_url)
        data = response.json()
        title = data["items"][0]["snippet"]["title"]
        # Sanitize title for filename
        title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
        return title or "video"
    except Exception as e:
        st.error(f"❌ Error fetching video title from YouTube API: {e}")
        return "video"

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

video_url = st.text_input("Enter YouTube video URL:", key="video_url_input")

if video_url != st.session_state.current_video_url:
    safe_rmtree("thumbs")
    os.makedirs("thumbs", exist_ok=True)

    for file in glob.glob("*.mp4"):
        os.remove(file)
    for file in glob.glob("*.pdf"):
        os.remove(file)

    st.session_state.download_complete = False
    st.session_state.thumbs_path = []
    st.session_state.selected_thumbs = []
    st.session_state.current_video_url = video_url
    st.session_state.video_title = ''
    st.rerun()

previous_mode = st.session_state.thumbnail_mode
st.session_state.thumbnail_mode = st.radio(
    "How do you want to extract thumbnails?",
    ("Automatic", "Manual"),
    help="Automatic: Every 30s. Manual: Input specific timestamps (e.g., 5:40, 10:22)."
)

if previous_mode != st.session_state.thumbnail_mode:
    st.session_state.download_complete = False
    st.session_state.thumbs_path = []
    st.session_state.selected_thumbs = []

manual_timestamps = []
if st.session_state.thumbnail_mode == "Manual":
    timestamps_input = st.text_input("Enter timestamps (MM:SS, comma-separated):", placeholder="5:40, 10:22")
    if timestamps_input:
        try:
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

thumbs_per_page = st.slider("Number of thumbnails per PDF page (recommended 6):", 2, 12, 6)

if st.button("Download Video & Generate Thumbnails"):
    if video_url:
        safe_rmtree("thumbs")
        os.makedirs("thumbs", exist_ok=True)

        for file in glob.glob("*.mp4"):
            os.remove(file)
        for file in glob.glob("*.pdf"):
            os.remove(file)

        video_title = fetch_video_title(video_url)
        st.session_state.video_title = video_title
        video_file = f"{video_title}.mp4"

        try:
            st.info("📥 Downloading video...")
            subprocess.run(["yt-dlp", "-f", "mp4", "-o", video_file, video_url], check=True)
            st.success("✅ Video downloaded!")
        except Exception as e:
            st.error(f"❌ Error downloading video: {e}")
            st.stop()

        reencoded_file = f"reencoded_{video_title}.mp4"
        try:
            st.info("🔄 Re-encoding video for compatibility...")
            subprocess.run([
                "ffmpeg", "-y", "-i", video_file,
                "-c:v", "libx264", "-c:a", "aac", reencoded_file
            ], check=True)
            st.success("✅ Re-encoded successfully!")
            video_file = reencoded_file
        except Exception as e:
            st.error(f"❌ Error re-encoding video: {e}")
            st.stop()

        st.info("🖼️ Generating thumbnails...")
        if st.session_state.thumbnail_mode == "Automatic":
            os.system(f"ffmpeg -y -i {video_file} -vf fps=1/30 thumbs/thumb_%03d.jpg")
            thumbs = sorted([f for f in os.listdir("thumbs") if f.endswith(".jpg")])
            st.session_state.thumbs_path = [os.path.join("thumbs", t) for t in thumbs]
            st.session_state.download_complete = True
            st.session_state.selected_thumbs = []
        else:
            if not manual_timestamps:
                st.error("Please enter valid timestamps.")
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
            st.error("No thumbnails generated.")
            st.stop()
    else:
        st.warning("Please enter a valid YouTube URL.")

if st.session_state.download_complete and st.session_state.thumbs_path and st.session_state.current_video_url == video_url:
    st.write("### Thumbnails:")
    cols = st.columns(2)
    
    for i, thumb in enumerate(st.session_state.thumbs_path):
        with cols[i % 2]:
            caption = f"{i*30} sec" if st.session_state.thumbnail_mode == "Automatic" else \
                      f"{manual_timestamps[i] // 60}:{manual_timestamps[i] % 60:02d}" if i < len(manual_timestamps) else "Unknown"
            st.image(thumb, caption=caption)
            if st.button(f"Add to PDF - {caption}", key=f"btn_{i}"):
                if (thumb, caption) not in st.session_state.selected_thumbs:
                    st.session_state.selected_thumbs.append((thumb, caption))
                    st.rerun()

    if st.session_state.selected_thumbs:
        st.write("Selected for PDF:")
        for thumb in st.session_state.selected_thumbs:
            st.write(f"- {thumb[1]}")

        if st.button("📄 Generate PDF"):
            for file in glob.glob("*.pdf"):
                os.remove(file)

            pdf = FPDF()
            for page_num in range(0, len(st.session_state.selected_thumbs), thumbs_per_page):
                pdf.add_page()
                pdf.set_font("Arial", "B", size=14)
                pdf.cell(0, 10, st.session_state.video_title, ln=True, align="C")
                pdf.set_font("Arial", size=12)
                pdf.ln(10)
                page_thumbs = st.session_state.selected_thumbs[page_num:page_num+thumbs_per_page]
                for i, (img_path, caption) in enumerate(page_thumbs):
                    x = 10 + (i % 2) * 100
                    y = 30 + (i // 2) * 100
                    pdf.text(x, y-5, caption)
                    pdf.image(img_path, x=x, y=y, w=90, h=60)
            pdf_file = f"{st.session_state.video_title}_thumbnails.pdf"
            pdf.output(pdf_file)
            with open(pdf_file, "rb") as f:
                st.download_button("⬇️ Download PDF", f, pdf_file)
