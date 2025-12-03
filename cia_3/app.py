import os
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import traceback
import io, base64, requests
from sqlalchemy import text
from db import engine
import json
from datetime import datetime

load_dotenv()

app = FastAPI(title="Visora")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


ROBOFLOW_API_URL = "https://serverless.roboflow.com"
ROBOFLOW_API_KEY = "9wcvpzPwDMVxzcrPYsgn"
MODEL_ID = "car-damage-detection-sklxm-p2h6s/1"

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        response = requests.post(
            f"{ROBOFLOW_API_URL}/{MODEL_ID}",
            params={"api_key": ROBOFLOW_API_KEY},
            files={"file": ("image.jpg", image_bytes, "image/jpeg")}
        )
        data = response.json()
        predictions = data.get("predictions", [])

        # Обработак
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("arial.ttf", 26)
        except:
            font = ImageFont.load_default()

        COLORS = {
            "scratch": (255, 215, 0),
            "dent": (255, 69, 58),
            "rust": (255, 140, 0),
            "crack": (138, 43, 226),
            "default": (75, 0, 130)
        }
        for pred in predictions:
            if "bbox" in pred:
                x = pred["bbox"]["x_center"]
                y = pred["bbox"]["y_center"]
                w = pred["bbox"]["width"]
                h = pred["bbox"]["height"]
            else:
                x = pred.get("x")
                y = pred.get("y")
                w = pred.get("width")
                h = pred.get("height")

            if None in (x, y, w, h):
                print("Пропуск:", pred)
                continue

            left, top = x - w / 2, y - h / 2
            right, bottom = x + w / 2, y + h / 2

            label = pred["class"]
            color = COLORS.get(label.lower(), COLORS["default"])

            draw.rectangle([left, top, right, bottom], outline=color, width=5)

            # текст 
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), label, font=font)
                text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            else:
                text_w, text_h = draw.textsize(label, font=font)

            draw.rectangle(
                [left, max(0, top - text_h - 6), left + text_w + 10, top],
                fill=color
            )
            draw.text((left + 5, top - text_h - 4), label, fill="white", font=font)
        buf = io.BytesIO()
        image.save(buf, format="JPEG")
        image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO analysis_history (filename, type, json, created_at)
                        VALUES (:filename, :type, :json, :created_at)
                    """),
                    {
                        "filename": file.filename,
                        "type": "analyze",
                        "json": json.dumps(predictions),
                        "created_at": datetime.utcnow()
                    }
                )
                conn.commit()
                print("сохранено в БД")
        except Exception as db_err:
            print("Ошибка сохранения:", db_err)
        return templates.TemplateResponse("result.html", {
            "request": request,
            "result": predictions,
            "image_data": image_base64
        })

    except Exception as e:
        traceback.print_exc()

        return templates.TemplateResponse("result.html", {
            "request": request,
            "result": f"Ошибка: {e}",
            "image_data": None
        })



@app.get("/main_v", response_class=HTMLResponse)
def gla(request: Request):
    return templates.TemplateResponse("main_v.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
def analyze(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/gid", response_class=HTMLResponse)
def gid(request: Request):
    return templates.TemplateResponse("gid.html", {"request": request})

@app.get("/faq", response_class=HTMLResponse)
def gid(request: Request):
    return templates.TemplateResponse("faq.html", {"request": request})
