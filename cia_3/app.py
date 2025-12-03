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
# MODEL_ID = "nikita-1bgwc/cai-jwunu-instant-22"
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

        # for pred in predictions:
        #     x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
        #     left, top = x - w / 2, y - h / 2
        #     right, bottom = x + w / 2, y + h / 2
        #     label = pred["class"]

        #     color = COLORS.get(label.lower(), COLORS["default"])
        #     draw.rectangle([left, top, right, bottom], outline=color, width=5)

        #     if hasattr(draw, "textbbox"):
        #         bbox = draw.textbbox((0, 0), label, font=font)
        #         text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        #     else:
        #         text_w, text_h = draw.textsize(label, font=font)

        #     draw.rectangle(
        #         [left, max(0, top - text_h - 6), left + text_w + 10, top],
        #         fill=color
        #     )
            # draw.text((left + 5, top - text_h - 4), label, fill="white", font=font)

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

            # текст на фто
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










# from ultralytics import YOLO
# import numpy as np



# from fastapi import FastAPI, Request, UploadFile, File
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from sqlalchemy import text
# from db import engine

# from ultralytics import YOLO
# from PIL import Image, ImageDraw, ImageFont
# from datetime import datetime
# import io, base64, json, traceback

# app = FastAPI()
# templates = Jinja2Templates(directory="templates")

# # Загружаем обученную модель YOLO11 (укажи путь к своему .pt)
# model = YOLO("best.pt")

# # Главная страница
# @app.get("/", response_class=HTMLResponse)
# def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


# # Основная функция анализа
# @app.post("/analyze", response_class=HTMLResponse)
# async def analyze(request: Request, file: UploadFile = File(...)):
#     try:
#         # Читаем изображение
#         image_bytes = await file.read()
#         image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

#         # Предсказание через YOLO
#         # results = model.predict(source=image, stream=False, imgsz=640)

#         # predictions = []
#         # for r in results:
#         #     for box in r.boxes:
#         #         cls = model.names[int(box.cls)]
#         #         x1, y1, x2, y2 = box.xyxy[0].tolist()
#         #         predictions.append({
#         #             "class": cls,
#         #             "x": (x1 + x2) / 2,
#         #             "y": (y1 + y2) / 2,
#         #             "width": x2 - x1,
#         #             "height": y2 - y1
#         #         })


#         results = model.predict(source=image_bytes, imgsz=640, conf=0.25, save=False, verbose=False)

#         predictions = []
#         for box in results[0].boxes:
#             cls = int(box.cls[0])
#             label = model.names[cls]
#             x_center, y_center, w, h = box.xywh[0].tolist()
#             predictions.append({
#                 "class": label,
#                 "x": x_center,
#                 "y": y_center,
#                 "width": w,
#                 "height": h
#             })
            
#         # Отрисовка
#         draw = ImageDraw.Draw(image)
#         try:
#             font = ImageFont.truetype("arial.ttf", 26)
#         except:
#             font = ImageFont.load_default()

#         COLORS = {
#             "scratch": (255, 215, 0),
#             "dent": (255, 69, 58),
#             "rust": (255, 140, 0),
#             "crack": (138, 43, 226),
#             "default": (75, 0, 130)
#         }

#         for pred in predictions:
#             x, y, w, h = pred["x"], pred["y"], pred["width"], pred["height"]
#             left, top = x - w / 2, y - h / 2
#             right, bottom = x + w / 2, y + h / 2
#             label = pred["class"]

#             color = COLORS.get(label.lower(), COLORS["default"])
#             draw.rectangle([left, top, right, bottom], outline=color, width=5)

#             if hasattr(draw, "textbbox"):
#                 bbox = draw.textbbox((0, 0), label, font=font)
#                 text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
#             else:
#                 text_w, text_h = draw.textsize(label, font=font)

#             draw.rectangle(
#                 [left, max(0, top - text_h - 6), left + text_w + 10, top],
#                 fill=color
#             )
#             draw.text((left + 5, top - text_h - 4), label, fill="white", font=font)

#         # Преобразуем итоговое изображение в base64
#         buf = io.BytesIO()
#         image.save(buf, format="JPEG")
#         image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

#         # Сохраняем результаты в базу
#         try:
#             with engine.connect() as conn:
#                 conn.execute(
#                     text("""
#                         INSERT INTO analysis_history (filename, type, json, created_at)
#                         VALUES (:filename, :type, :json, :created_at)
#                     """),
#                     {
#                         "filename": file.filename,
#                         "type": "analyze",
#                         "json": json.dumps(predictions),
#                         "created_at": datetime.utcnow()
#                     }
#                 )
#                 conn.commit()
#                 print("✅ Данные успешно сохранены в БД")
#         except Exception as db_err:
#             print("❌ Ошибка сохранения в базу:", db_err)

#         # Возврат шаблона с результатом
#         return templates.TemplateResponse("result.html", {
#             "request": request,
#             "result": predictions,
#             "image_data": image_base64
#         })

#     except Exception as e:
#         traceback.print_exc()
#         return templates.TemplateResponse("result.html", {
#             "request": request,
#             "result": f"Ошибка: {e}",
#             "image_data": None
#         })
