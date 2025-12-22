import io
import time
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from minio import Minio
from minio.error import S3Error
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
    print(f"Модель загружена: {MODEL_PATH}")
except Exception:
    try:
        import pickle
        with open(MODEL_PATH, 'rb') as f:
            loaded_model = pickle.load(f)
        print(f"Модель загружена (pickle): {MODEL_PATH}")
    except Exception as e:
        print(f"Ошибка загрузки модели: {e}")
        raise SystemExit("Критическая ошибка: модель не найдена")

class FileRequest(BaseModel):
    filename: str

@app.post("/predict")
def run_prediction(request: FileRequest):
    if minio_client is None:
        raise HTTPException(status_code=500, detail="Нет подключения к MinIO")

    filename = request.filename
    print(f"Обработка файла: {filename}")

    try:
        # 1. Скачивание файла
        try:
            response = minio_client.get_object(BUCKET_RAW, filename)
            data = response.read()
            response.close()
            response.release_conn()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(status_code=404, detail=f"Файл {filename} не найден")
            raise

        # 2. Чтение (header=None, так как в файле только цифры)
        df = pd.read_csv(
            io.BytesIO(data), 
            sep=r"\s+", 
            names=["x", "y", "z"],
            header=None  
        )

        if df.empty:
            raise HTTPException(status_code=400, detail="Файл пустой")

        # 3. Предсказание
        start = time.time()
        predictions = loaded_model.predict(df[["x", "y", "z"]])
        duration = time.time() - start

        # 4. Формирование порядка: class на первом месте
        df.insert(0, 'class', predictions)

        output_data = df.to_csv(sep=" ", header=False, index=False).encode('utf-8')
        output_buffer = io.BytesIO(output_data)

        result_filename = f"predicted_{filename}"
        
        minio_client.put_object(
            BUCKET_PREDICTED,
            result_filename,
            output_buffer,
            length=len(output_data),
            content_type="text/plain"
        )

        return {
            "status": "success",
            "original_file": filename,
            "result_file": result_filename,
            "rows_processed": len(df),
            "prediction_time": round(duration, 3)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)