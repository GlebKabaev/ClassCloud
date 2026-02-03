import io
import time
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from minio import Minio
import uvicorn
import joblib
from catboost import CatBoostClassifier

# Настройки
MINIO_ENDPOINT = "127.0.0.1:9002"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
SECURE_CONNECTION = False

MODEL_PATH_RF = "random_fotest_trained_third.pkl"
MODEL_PATH_CB = "cpu_catboost_model.cbm"

BUCKET_RAW = "raw"
BUCKET_PREDICTED = "predicted"

app = FastAPI(title="ML Multi-Model Service")

# Глобальные переменные для MinIO и моделей
minio_client = None
rf_model = None
cb_model = None

def init_service():
    global minio_client, rf_model, cb_model
    print("\n" + "="*50)
    print(">>> ИНИЦИАЛИЗАЦИЯ СЕРВИСА")
    print("="*50)

    try:
        # 1. Подключение к MinIO
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=SECURE_CONNECTION,
            region="us-east-1"
        )
        print(f"[v] Соединение с MinIO установлено: {MINIO_ENDPOINT}")

        # 2. Проверка и создание бакетов
        for bucket in [BUCKET_RAW, BUCKET_PREDICTED]:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                print(f"[+] Бакет '{bucket}' не найден. Создан новый.")
            else:
                print(f"[v] Бакет '{bucket}' обнаружен и готов к работе.")

        # 3. Загрузка моделей
        print(f"[*] Загрузка модели RF из {MODEL_PATH_RF}...")
        rf_model = joblib.load(MODEL_PATH_RF)
        print("[v] Модель Random Forest успешно загружена.")

        print(f"[*] Загрузка модели CatBoost из {MODEL_PATH_CB}...")
        cb_model = CatBoostClassifier()
        cb_model.load_model(MODEL_PATH_CB)
        print("[v] Модель CatBoost успешно загружена.")
        
        print("="*50)
        print(">>> СЕРВИС ПОЛНОСТЬЮ ГОТОВ К РАБОТЕ")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n[!!!] КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")
        raise

# Запуск инициализации
init_service()

class FileRequest(BaseModel):
    filename: str

def apply_pipeline_v2(df):
    """Реализация пайплайна V2 для модели CatBoost"""
    res = df.copy().reset_index(drop=True)
    res['scene_id'] = 'current_batch'

    for col in ['x', 'y', 'z']:
        res[f'{col}_norm'] = res.groupby('scene_id')[col].transform(lambda x: (x - x.mean()) / (x.std() + 1e-6))

    grid_size = 1.0
    res['grid_x'] = (res['x'] / grid_size).astype(int)
    res['grid_y'] = (res['y'] / grid_size).astype(int)

    group = res.groupby(['scene_id', 'grid_x', 'grid_y'])['z']
    
    res['z_min'] = group.transform('min')
    res['z_max'] = group.transform('max')
    res['z_std'] = group.transform('std')
    res['z_rel'] = res['z'] - res['z_min']
    res['z_range'] = res['z_max'] - res['z_min']
    res['density'] = group.transform('count')
    
    res['dist_origin'] = np.sqrt(res['x_norm']**2 + res['y_norm']**2)
    res.fillna(0, inplace=True)
    
    feature_cols = ['x_norm', 'y_norm', 'z_norm', 'z_rel', 'z_range', 'z_std', 'density', 'dist_origin']
    return res[feature_cols]

@app.post("/predict")
def run_prediction(request: FileRequest):
    if minio_client is None:
        raise HTTPException(status_code=500, detail="MinIO не подключен")

    filename = request.filename
    print(f"\n[!] ПОЛУЧЕН ЗАПРОС на файл: {filename}")

    is_landscape = "landscape" in filename.lower()

    try:
        # 1. Скачивание файла из MinIO
        print(f"[*] Скачивание '{filename}' из бакета '{BUCKET_RAW}'...")
        response = minio_client.get_object(BUCKET_RAW, filename)
        data = response.read()
        response.close()
        print(f"[v] Файл скачан успешно ({len(data)} байт).")

        # 2. Чтение файла
        df = pd.read_csv(
            io.BytesIO(data), 
            sep=r"\s+", 
            names=["class", "x", "y", "z"],
            header=None  
        )

        if df.empty:
            print(f"[X] Ошибка: файл {filename} пуст.")
            raise HTTPException(status_code=400, detail="Файл пустой")

        start_time = time.time()

        # 3. Логика выбора модели и пайплайна
        if is_landscape:
            print(f"[*] Тип файла определен как LANDSCAPE. Запуск пайплайна V2...")
            X_features = apply_pipeline_v2(df)
            print(f"[*] Генерация признаков завершена. Запуск предсказания CatBoost...")
            predictions = cb_model.predict(X_features).flatten()
            model_name = "CatBoost_V2"
        else:
            print(f"[*] Тип файла: СТАНДАРТ. Запуск предсказания Random Forest (координаты x,y,z)...")
            predictions = rf_model.predict(df[["x", "y", "z"]])
            model_name = "RandomForest_Raw"

        duration = time.time() - start_time

        # 4. Подготовка результата
        df['class'] = predictions
        output_data = df[['class', 'x', 'y', 'z']].to_csv(sep=" ", header=False, index=False).encode('utf-8')
        
        # 5. Выгрузка в MinIO
        result_filename = f"predicted_{filename}"
        print(f"[*] Загрузка результата '{result_filename}' в бакет '{BUCKET_PREDICTED}'...")
        minio_client.put_object(
            BUCKET_PREDICTED,
            result_filename,
            io.BytesIO(output_data),
            length=len(output_data),
            content_type="text/plain"
        )

        # Итоговый лог
        print(f"[v] УСПЕХ: {filename} обработан.")
        print(f"    - Использована модель: {model_name}")
        print(f"    - Время расчета: {round(duration, 3)} сек.")
        print(f"    - Результат: {result_filename}")

        return {
            "status": "success",
            "used_model": model_name,
            "prediction_time": round(duration, 3),
            "result_file": result_filename
        }

    except Exception as e:
        print(f"[X] ОШИБКА при обработке {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)