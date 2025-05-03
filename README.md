🎥 YT SnapPDF - YouTube Thumbnail to PDF Converter
YT SnapPDF is a Streamlit-based web app that allows users to extract thumbnails from YouTube videos (either automatically or manually), select their favorites, and generate a downloadable PDF with those thumbnails and timestamps.

🚀 Features
🔗 Enter any YouTube video URL.

⚙️ Choose thumbnail extraction mode:

Automatic: Captures every 30 seconds.

Manual: Specify exact timestamps (e.g., 1:30, 3:45, 5:00).

🖼️ Preview all generated thumbnails.

✅ Select the thumbnails you want to include in your PDF.

🧾 Generate a clean, multi-page PDF with video title, thumbnails, and timestamps.

📥 Download the final PDF.

🛠️ Tech Stack
Streamlit – Frontend UI

yt-dlp – Download YouTube videos

FFmpeg – Generate video thumbnails

FPDF – Create downloadable PDF

Pillow – Image handling

⚡ Requirements
Ensure the following are installed on your system:

Python 3.7+

yt-dlp

ffmpeg

Python packages from requirements.txt

bash
Copy
Edit
pip install -r requirements.txt
🧪 Run Locally
bash
Copy
Edit
streamlit run app.py
🌐 Deploy on Streamlit Cloud
Create a public GitHub repo and push this app.

Go to Streamlit Cloud and connect your repo.

Click "Deploy".

📌 Notes
App resets on new URL or mode switch.

PDF includes 2–12 thumbnails per page (adjustable).

All temporary files auto-cleaned between runs.

👨‍💻 Author
Built by Akash Sahu — GitHub @akashsahu54
