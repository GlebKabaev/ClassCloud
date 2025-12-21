import io
import time
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from minio import Minio
from minio.error import S3Error  # Импорт для обработки ошибок MinIO
import uvicorn

# Настройки
MINIO_ENDPOINT = "127.0.0.1:9002"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
SECURE_CONNECTION = False

MODEL_PATH = "random_fotest_trained_third.pkl"
BUCKET_RAW = "raw"
BUCKET_PREDICTED = "predicted"

# Инициализация приложения
app = FastAPI(title="ML Prediction Service")

# Подключение к MinIO
minio_client = None
try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=SECURE_CONNECTION,
        region="us-east-1"
    )
    # Проверка соединения
    minio_client.list_buckets()
    print(f"Подключено к MinIO: {MINIO_ENDPOINT}")

    for bucket in [BUCKET_RAW, BUCKET_PREDICTED]:
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
            print(f"Создан бакет: {bucket}")
except Exception as e:
    print(f"Ошибка MinIO: {e}")
    minio_client = None

# Загрузка модели
loaded_model = None
try:
    from joblib import load as joblib_load
    loaded_model = joblib_load(MODEL_PATH)
    print(f"Модель загружена через joblib: {MODEL_PATH}")
except Exception:
    try:
        import pickle
        with open(MODEL_PATH, 'rb') as f:
            loaded_model = pickle.load(f)
        print(f"Модель загружена через pickle: {MODEL_PATH}")
    except Exception as e:
        print(f"Не удалось загрузить модель: {e}")
        raise SystemExit("Ошибка загрузки модели")

# Проверка метода предсказания
if not hasattr(loaded_model, "predict"):
    raise SystemExit("Загруженный объект не имеет метода predict")

class FileRequest(BaseModel):
    filename: str

@app.post("/predict")
def run_prediction(request: FileRequest):
    if minio_client is None:
        raise HTTPException(status_code=500, detail="Нет подключения к MinIO")

    filename = request.filename
    print(f"Обработка файла: {filename}")

    try:
        try:
            response = minio_client.get_object(BUCKET_RAW, filename)
            data = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(status_code=404, detail=f"Файл {filename} не найден в бакете {BUCKET_RAW}")
            raise


        df = pd.read_csv(
            io.BytesIO(data), 
            sep=r"\s+", 
            names=["x", "y", "z"],
            header=0  
        )

        if df.empty:
            raise HTTPException(status_code=400, detail="Файл пустой")

        start = time.time()
        predictions = loaded_model.predict(df[["x", "y", "z"]])
        duration = time.time() - start

        df['class'] = predictions
        df = df[['class', 'x', 'y', 'z']]

        csv_bytes = df.to_csv(index=False).encode('utf-8')
        csv_buffer = io.BytesIO(csv_bytes)

        result_filename = f"predicted_{filename}"
        minio_client.put_object(
            BUCKET_PREDICTED,
            result_filename,
            csv_buffer,
            length=len(csv_bytes),
            content_type="application/csv"
        )

        print(f"Результат сохранён: {result_filename}")

        return {
            "status": "success",
            "original_file": filename,
            "result_file": result_filename,
            "rows_processed": len(df),
            "prediction_time_sec": round(duration, 3)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)