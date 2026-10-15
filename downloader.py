from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI(title="One Team Downloader API")

class LinkRequest(BaseModel):
    url: str

def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/api/download")
def download_video(req: LinkRequest, bg_tasks: BackgroundTasks):
    try:
        file_id = str(uuid.uuid4())
        out_tmpl = f"/tmp/{file_id}.%(ext)s"
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': out_tmpl,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            filepath = ydl.prepare_filename(info)
            if not os.path.exists(filepath):
                filepath = filepath.rsplit('.', 1)[0] + '.mp4'
                
        if os.path.exists(filepath):
            bg_tasks.add_task(remove_file, filepath)
            return FileResponse(filepath, media_type="video/mp4", filename="video.mp4")
        else:
            raise HTTPException(status_code=500, detail="Video ဒေါင်းလုဒ် မအောင်မြင်ပါ")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
