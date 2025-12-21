import express from 'express'
import cors from 'cors'
import multer from 'multer'
import { Client as MinioClient } from 'minio'

const app = express()
const upload = multer({ storage: multer.memoryStorage() })

const {
  MINIO_ENDPOINT = '127.0.0.1',
  // Порт MinIO на хосте (по docker-compose проброшен 9002 -> 9000 в контейнере)
  MINIO_PORT = '9002',
  MINIO_USE_SSL = 'false',
  MINIO_ACCESS_KEY = 'minioadmin',
  MINIO_SECRET_KEY = 'minioadmin',
  MINIO_RAW_BUCKET = 'raw',
  MINIO_PREDICTED_BUCKET = 'predicted',
  SERVER_PORT = '4000',
} = process.env

const minioClient = new MinioClient({
  endPoint: MINIO_ENDPOINT,
  port: Number(MINIO_PORT),
  useSSL: MINIO_USE_SSL === 'true',
  accessKey: MINIO_ACCESS_KEY,
  secretKey: MINIO_SECRET_KEY,
})

const allowedOrigins = [
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'http://localhost:5174',
  'http://127.0.0.1:5174',
]

app.use(cors({ origin: allowedOrigins, credentials: false }))

async function ensureBucket(bucket) {
  const exists = await minioClient.bucketExists(bucket).catch(() => false)
  if (!exists) {
    await minioClient.makeBucket(bucket, 'us-east-1')
  }
}

app.post('/api/classify/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'Файл не найден' })
    }

    await ensureBucket(MINIO_RAW_BUCKET)

    const objectName = `${Date.now()}-${req.file.originalname}`

    await minioClient.putObject(
      MINIO_RAW_BUCKET,
      objectName,
      req.file.buffer,
      req.file.size,
      { 'Content-Type': req.file.mimetype }
    )

    // Запускаем обработку в фоне (не ждем результата)
    fetch('http://127.0.0.1:8001/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: objectName }),
    })
      .then((response) => {
        if (response.ok) {
          return response.json()
        } else {
          console.error('Ошибка обработки файла:', response.status, response.statusText)
          return null
        }
      })
      .then((result) => {
        if (result) {
          console.log('Файл обработан, результат:', result.result_file)
        }
      })
      .catch((err) => {
        console.error('Ошибка вызова сервиса предсказаний:', err)
      })

    // Сразу возвращаем ответ о загрузке файла
    return res.json({
      message: 'Файл загружен, нажмите на кнопку Скачать',
      objectName,
      statusUrl: `/api/classify/status/${objectName}`,
    })
  } catch (error) {
    console.error('Ошибка загрузки в MinIO:', error)
    return res.status(500).json({ message: 'Не удалось загрузить файл' })
  }
})

// Эндпоинт для проверки статуса и скачивания обработанного файла
app.get('/api/classify/status/:filename', async (req, res) => {
  try {
    const { filename } = req.params
    const resultFileName = `predicted_${filename}`

    await ensureBucket(MINIO_PREDICTED_BUCKET)

    // Проверяем, существует ли обработанный файл
    try {
      await minioClient.statObject(MINIO_PREDICTED_BUCKET, resultFileName)

      // Файл готов, скачиваем его
      const dataStream = await minioClient.getObject(
        MINIO_PREDICTED_BUCKET,
        resultFileName
      )

      // Собираем данные из потока
      const chunks = []
      for await (const chunk of dataStream) {
        chunks.push(chunk)
      }
      const fileBuffer = Buffer.concat(chunks)

      // Отправляем файл пользователю для автоматического скачивания
      res.setHeader('Content-Type', 'text/csv')
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="${resultFileName}"`
      )
      res.setHeader('Content-Length', fileBuffer.length)
      return res.send(fileBuffer)
    } catch (statError) {
      // Файл еще не готов
      if (statError.code === 'NotFound' || statError.code === 'NoSuchKey') {
        return res.status(202).json({
          status: 'processing',
          message: 'Файл еще обрабатывается',
          filename,
        })
      }
      throw statError
    }
  } catch (error) {
    console.error('Ошибка проверки статуса файла:', error)
    return res.status(500).json({
      message: 'Ошибка при проверке статуса файла',
      error: error.message,
    })
  }
})

app.listen(Number(SERVER_PORT), () => {
  console.log(`API server listening on http://localhost:${SERVER_PORT}`)
})

