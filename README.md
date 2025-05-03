# 🎥 YT SnapPDF - YouTube video to PDF Converter

**YT SnapPDF** is a Streamlit-based web app that allows users to extract images/frames from YouTube videos (either automatically or manually), select their favourites, and generate a downloadable PDF with those frames and timestamps.

**web app link** : https://ytvideotopdf777.streamlit.app/ 
---

## 🚀 Features

- 🔗 Enter any YouTube video URL.
- ⚙️ Choose frames extraction mode:
  - **Automatic**: Captures every 30 seconds.
  - **Manual**: Specify exact timestamps (e.g., `1:30, 3:45, 5:00`).
- 🖼️ Preview all generated frames.
- ✅ Select the frames you want to include in your PDF.
- 🧾 Generate a **clean, multi-page PDF** with video title, frames, and timestamps.
- 📥 Download the final PDF.

---

## 🛠️ Tech Stack

- `Streamlit` – Frontend UI
- `yt-dlp` – Download YouTube videos
- `FFmpeg` – Generate video frames
- `FPDF` – Create downloadable PDF
- `Pillow` – Image handling

---

## ⚡ Requirements

Ensure the following are installed on your system:

- Python 3.10.x
- `yt-dlp`
- `ffmpeg`
