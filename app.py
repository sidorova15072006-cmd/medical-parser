from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import tempfile
from faster_whisper import WhisperModel
from parser import extract_data

app = FastAPI(title="Medical Speech Parser", docs_url="/docs")

# Разрешаем доступ для всех устройств в сети
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("=" * 60)
print("Загрузка модели Whisper (small)...")
print("Модель скачается один раз. Подождите 1-2 минуты.")
print("=" * 60)

# Используем модель "small" - быстро и надёжно
model = WhisperModel("small", device="cpu", compute_type="int8")

print("=" * 60)
print("Модель готова! Сервер запущен.")
print("Откройте в браузере: http://localhost:8000/docs")
print("Для других пользователей: http://192.168.1.136:8000/docs")
print("=" * 60)

@app.get("/")
async def root():
    return {
        "service": "Medical Speech Parser",
        "status": "online",
        "message": "Сервис работает. Используйте /docs для тестирования"
    }

@app.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    """Отправьте аудиофайл (.wav или .mp3) с речью пациента"""
    
    # Проверка формата
    if not file.filename.endswith(('.wav', '.mp3')):
        return {"error": "Поддерживаются только файлы .wav и .mp3"}
    
    # Сохраняем временный файл
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name
    
    try:
        # Распознаём речь
        segments, _ = model.transcribe(temp_path, language="ru", beam_size=5)
        text = " ".join([s.text for s in segments]).strip()
        
        if not text:
            return {"error": "Не удалось распознать речь"}
        
        # Извлекаем структурированные данные
        result = extract_data(text)
        
        return {
            "status": "success",
            "transcript": text,
            "medical_record": result
        }
    
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}"}
    
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.post("/test")
async def test():
    """Тестовый эндпоинт без аудио"""
    test_text = "Меня зовут Иван Петрович, мне 45 лет. У меня болит спина в пояснице, боль отдает в левую ногу. Обезболивающие не помогают."
    result = extract_data(test_text)
    return {
        "test_text": test_text,
        "result": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)