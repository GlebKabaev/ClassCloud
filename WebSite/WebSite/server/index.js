import express from 'express'
import cors from 'cors'
import multer from 'multer'
import { Client as MinioClient } from 'minio'

const app = express()
const upload = multer({ storage: multer.memoryStorage() })

const {
  MINIO_ENDPOINT = '127.0.0.1',
  MINIO_PORT = '9000',
  MINIO_USE_SSL = 'false',
  MINIO_ACCESS_KEY = 'minioadmin',
  MINIO_SECRET_KEY = 'minioadmin',
  MINIO_RAW_BUCKET = 'raw',
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

    return res.json({ message: 'Файл загружен', objectName })
  } catch (error) {
    console.error('Ошибка загрузки в MinIO:', error)
    return res.status(500).json({ message: 'Не удалось загрузить файл' })
  }
})

app.listen(Number(SERVER_PORT), () => {
  console.log(`API server listening on http://localhost:${SERVER_PORT}`)
})

