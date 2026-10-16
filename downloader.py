from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI(title="One Team Video Downloader API")

# Website မှ လှမ်းပို့မည့် Data ပုံစံ
class LinkRequest(BaseModel):
    url: str
    action: str = "720p" # 'audio', '360p', '720p' ဟု Website မှ ရွေးချယ်ပေးပို့နိုင်သည်

# ဖိုင်ကို Website သို့ ပို့ပြီးပါက ဆာဗာမှ ပြန်ဖျက်မည့် Function
def remove_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.post("/api/download")
def download_video(req: LinkRequest, bg_tasks: BackgroundTasks):
    try:
        # ဆာဗာထဲတွင် ယာယီသိမ်းမည့် ဖိုင်နာမည်ကို ဖန်တီးခြင်း
        file_id = str(uuid.uuid4())
        out_tmpl = f"/tmp/{file_id}.%(ext)s"
        
        # yt-dlp Setting များ
        ydl_opts = {
            'quiet': True,
            'outtmpl': out_tmpl,
            'no_warnings': True,
            'cookiefile': 'cookies.txt' # YouTube IP ပိတ်ခြင်းကို ကာကွယ်ရန်
        }
        
        # Quality ရွေးချယ်မှုအပေါ် မူတည်၍ Format ပြောင်းလဲခြင်း
        if req.action == "audio": 
            ydl_opts['format'] = 'bestaudio/best'
        elif req.action == "360p": 
            ydl_opts['format'] = 'best[height<=360]/best'
        else: 
            ydl_opts['format'] = 'best[height<=720]/best'
            
        # ဗီဒီယိုကို ဆာဗာထဲသို့ ဒေါင်းလုဒ်ဆွဲခြင်း
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=True)
            filepath = ydl.prepare_filename(info)
            
            # အချို့ ဖိုင်အမျိုးအစားများအတွက် mp4 သို့ သေချာစေရန်
            if not os.path.exists(filepath):
                filepath = filepath.rsplit('.', 1)[0] + '.mp4'
                
        # ဒေါင်းလုဒ်ဆွဲပြီးကြောင်း သေချာပါက
        if os.path.exists(filepath):
            # Website ဆီ ဖိုင်ပို့ပြီးတာနဲ့ ယာယီဖိုင်ကို အလိုအလျောက် ပြန်ဖျက်မည်
            bg_tasks.add_task(remove_file, filepath)
            
            media_type = "audio/mpeg" if req.action == "audio" else "video/mp4"
            filename = f"download.{'mp3' if req.action == 'audio' else 'mp4'}"
            
            # Website (Frontend) ဆီသို့ ဗီဒီယိုဖိုင် ပြန်ပို့ပေးခြင်း
            return FileResponse(filepath, media_type=media_type, filename=filename)
        else:
            raise HTTPException(status_code=500, detail="Video ဖိုင်ကို ဆာဗာတွင် ရှာမတွေ့ပါ။")
            
    except Exception as e:
        # Error တက်ပါက အကြောင်းရင်း အတိအကျကို Website ဆီသို့ ပြန်ပို့ပေးမည်
        exact_error = str(e)
        raise HTTPException(status_code=400, detail=exact_error)
