<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

    import 'vue3-carousel/carousel.css'
    import { Carousel, Slide, Navigation } from 'vue3-carousel'

    const currentSlide = ref(0)

    const slideTo = (nextSlide) => (currentSlide.value = nextSlide)

    const galleryConfig = {
        itemsToShow: 1,
        wrapAround: true,
        slideEffect: 'fade',
        mouseDrag: false,
        touchDrag: false,
        height: 600,
    }

    const thumbnailsConfig = {
        height: 80,
        itemsToShow: 3,
        wrapAround: true,
        touchDrag: false,
        gap: 3,
    }

    const images2 = ['/src/assets/caruselImages/1.png', '/src/assets/caruselImages/2.png', '/src/assets/caruselImages/3.png'];

    const images = Array.from({ length: 3 }, (_, index) => ({
        id: index + 1,
        url: images2[index],
    }))

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000'

const isTrainingOpen = ref(false)
const isClassifyOpen = ref(false)

const dropzoneTrainingPlaceholder = 'Перетащите файл для обучения'
const dropzoneClassifyPlaceholder = 'Перетащите файл для классификации'

const dropzoneTrainingText = ref(dropzoneTrainingPlaceholder)
const dropzoneClassifyText = ref(dropzoneClassifyPlaceholder)

const trainingFileInputRef = ref(null)
const classifyFileInputRef = ref(null)

const trainingFile = ref(null)
const classifyFile = ref(null)

const classifyStatus = ref({ type: '', message: '' })
const isClassifyUploading = ref(false)
const uploadedObjectName = ref(null)
const isDownloading = ref(false)

function openTraining() {
  isTrainingOpen.value = true
}

function openClassify() {
  isClassifyOpen.value = true
}

function resetDropzone(type) {
  if (type === 'training') {
    dropzoneTrainingText.value = dropzoneTrainingPlaceholder
    trainingFile.value = null
    if (trainingFileInputRef.value) trainingFileInputRef.value.value = ''
  } else if (type === 'classify') {
    dropzoneClassifyText.value = dropzoneClassifyPlaceholder
    classifyFile.value = null
    if (classifyFileInputRef.value) classifyFileInputRef.value.value = ''
  }
}

function closeTraining() {
  isTrainingOpen.value = false
  resetDropzone('training')
}

function closeClassify() {
  isClassifyOpen.value = false
  resetDropzone('classify')
  classifyStatus.value = { type: '', message: '' }
  uploadedObjectName.value = null
}

function handleFiles(files, type) {
  if (files && files.length) {
    const name = files[0].name
    if (type === 'training') {
      dropzoneTrainingText.value = name
      trainingFile.value = files[0]
    } else if (type === 'classify') {
      dropzoneClassifyText.value = name
      classifyFile.value = files[0]
      classifyStatus.value = { type: '', message: '' }
    }
  }
}

function onDrop(event, type) {
  handleFiles(event.dataTransfer?.files, type)
}

function onFileChange(event, type) {
  handleFiles(event.target.files, type)
}

function onKeydown(e) {
  if (e.key === 'Escape') {
    if (isTrainingOpen.value) closeTraining()
    if (isClassifyOpen.value) closeClassify()
  }
}

async function submitClassify() {
  if (!classifyFile.value) {
    classifyStatus.value = { type: 'error', message: 'Выберите файл для отправки' }
    return
  }

  const formData = new FormData()
  formData.append('file', classifyFile.value)

  isClassifyUploading.value = true
  classifyStatus.value = { type: '', message: '' }

  try {
    const response = await fetch(`${API_BASE_URL}/api/classify/upload`, {
      method: 'POST',
      body: formData,
    })

    const responseData = await response.json().catch(() => null)

    if (!response.ok) {
      const serverMessage = responseData?.message || 'Не удалось загрузить файл'
      const serverDetails = responseData?.details
      throw new Error(serverDetails ? `${serverMessage} (${serverDetails})` : serverMessage)
    }

    classifyStatus.value = { type: 'success', message: responseData?.message || 'Файл отправлен' }
    uploadedObjectName.value = responseData?.objectName || null
    dropzoneClassifyText.value = dropzoneClassifyPlaceholder
    classifyFile.value = null
    if (classifyFileInputRef.value) classifyFileInputRef.value.value = ''
  } catch (error) {
    classifyStatus.value = { type: 'error', message: error.message || 'Не удалось отправить файл' }
  } finally {
    isClassifyUploading.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

async function downloadClassifiedFile() {
  if (!uploadedObjectName.value) {
    classifyStatus.value = { type: 'error', message: 'Не найден загруженный файл' }
    return
  }

  isDownloading.value = true
  classifyStatus.value = { type: '', message: '' }

  try {
    const response = await fetch(`${API_BASE_URL}/api/classify/status/${uploadedObjectName.value}`)

    if (response.status === 202) {
      classifyStatus.value = { type: 'error', message: 'Файл еще обрабатывается, попробуйте позже' }
      return
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new Error(errorData?.message || 'Не удалось скачать файл')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const contentDisposition = response.headers.get('Content-Disposition')
    const filenameMatch = contentDisposition?.match(/filename="?(.+?)"?$/i)
    const filename = filenameMatch ? filenameMatch[1] : `predicted_${uploadedObjectName.value}`
    
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    classifyStatus.value = { type: 'success', message: 'Файл успешно скачан' }
  } catch (error) {
    classifyStatus.value = { type: 'error', message: error.message || 'Не удалось скачать файл' }
  } finally {
    isDownloading.value = false
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="app-wrapper">
    <header>
      <div class="wrapper">
        <div class="header-block">
          <div class="logo">
            <a href="https://www.kubsu.ru/" target="_blank" rel="noopener">
              <img src="@/assets/logo.png" alt="Logo" class="logo-img" />
            </a>
          </div>
          <!-- <a href="#" class="header-button" @click.prevent="openTraining">Войти как администратор</a> -->
        </div>
      </div>
    </header>

    <!-- Banner -->
    <section class="banner">
      <div class="banner-overlay">
        <div class="wrapper">
          <div class="banner-content">
            <h1 class="banner-title">Классификация точек</h1>
            <p class="banner-subtitle">Метод вокселей</p>
            <div class="banner-buttons">
              <!--<a href="#" class="banner-button banner-button--secondary" @click.prevent="openTraining">Обучить</a> -->
              <a href="#" class="banner-button" @click.prevent="openClassify">Классифицировать</a>
            </div>
          </div>
        </div>
      </div>
    </section>
    <!-- /Banner -->

    <main class="main-content">
      <div class="wrapper">
        <section class="intro-section">
          <p class="intro-text">
            Сервис позволяет классифицировать облака точек с помощью метода вокселей:
            загрузите файл, дождитесь обработки и скачайте результат с присвоенными метками классов.
          </p>
        </section>

        <section class="steps-section">
          <h2 class="section-title">Как это работает</h2>
          <div class="steps-grid">
            <div class="step-card">
              <span class="step-num">1</span>
              <h3 class="step-title">Загрузите файл</h3>
              <p class="step-desc">Перетащите облако точек в окно классификации или выберите файл на компьютере.</p>
            </div>
            <div class="step-card">
              <span class="step-num">2</span>
              <h3 class="step-title">Обработка</h3>
              <p class="step-desc">Система анализирует данные методом вокселей и присваивает метки классов.</p>
            </div>
            <div class="step-card">
              <span class="step-num">3</span>
              <h3 class="step-title">Скачайте результат</h3>
              <p class="step-desc">После завершения обработки скачайте файл с результатами классификации.</p>
            </div>
          </div>
        </section>

        <div class="main-block">
              <h2 class="banner-subSubtitle">Результат работы</h2>
              <p class="gallery-caption">Примеры визуализации классифицированных облаков точек.</p>
              <Carousel id="gallery" v-bind="galleryConfig" v-model="currentSlide">
                  <Slide v-for="image in images" :key="image.id">
                      <img :src="image.url" alt="Gallery Image" class="gallery-image" />
                  </Slide>
              </Carousel>

              <Carousel id="thumbnails" v-bind="thumbnailsConfig" v-model="currentSlide">
                  <Slide v-for="image in images" :key="image.id">
                      <template #default="{ currentIndex, isActive }">
                          <div :class="['thumbnail', { 'is-active': isActive }]"
                               @click="slideTo(currentIndex)">
                              <img :src="image.url" alt="Thumbnail Image" class="thumbnail-image" />
                          </div>
                      </template>
                  </Slide>

                  <template #addons>
                      <Navigation />
                  </template>
              </Carousel>

        </div>
      </div>
    </main>

    <footer>
      <div class="wrapper footer-box">
        <div class="footer-block">
          <p class="footer-title">Разработчики</p>
          <p>Команда 11</p>
        </div>
        <div class="footer-block">
          <p class="footer-title">Источники</p>
          <a href="https://github.com/GlebKabaev/ClassCloud.git" target="_blank" rel="noopener">GitHub</a>
        </div>
        <div class="footer-block">
        </div>
      </div>
    </footer>

    <!-- Training Popup -->
    <div v-if="isTrainingOpen" class="modal-overlay" @click.self="closeTraining">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Обучение</div>
          <button class="modal-close" @click="closeTraining" aria-label="Закрыть">×</button>
        </div>
        <div class="modal-body">
          <label
            class="dropzone"
            @dragover.prevent
            @dragenter.prevent
            @drop.prevent="onDrop($event, 'training')"
          >
            <span>{{ dropzoneTrainingText }}</span>
            <input
              ref="trainingFileInputRef"
              type="file"
              class="dropzone-input"
              @change="onFileChange($event, 'training')"
            />
          </label>
          <div class="modal-actions">
            <button type="button" class="popup-button">Добавить</button>
          </div>
        </div>
      </div>
    </div>
    <!-- /Training Popup -->

    <!-- Classify Popup -->
    <div v-if="isClassifyOpen" class="modal-overlay" @click.self="closeClassify">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Классификация</div>
          <button class="modal-close" @click="closeClassify" aria-label="Закрыть">×</button>
        </div>
        <div class="modal-body">
          <label
            class="dropzone"
            @dragover.prevent
            @dragenter.prevent
            @drop.prevent="onDrop($event, 'classify')"
          >
            <span>{{ dropzoneClassifyText }}</span>
            <input
              ref="classifyFileInputRef"
              type="file"
              class="dropzone-input"
              @change="onFileChange($event, 'classify')"
            />
          </label>
          <p
            v-if="classifyStatus.message"
            :class="['status-message', `status-message--${classifyStatus.type}`]"
          >
            {{ classifyStatus.message }}
          </p>
          <div class="modal-actions">
            <button
              type="button"
              class="popup-button"
              :disabled="isClassifyUploading"
              @click="submitClassify"
            >
              {{ isClassifyUploading ? 'Отправка...' : 'Отправить' }}
            </button>
            <button
              v-if="uploadedObjectName && classifyStatus.type === 'success'"
              type="button"
              class="popup-button popup-button--secondary"
              :disabled="isDownloading"
              @click="downloadClassifiedFile"
            >
              {{ isDownloading ? 'Скачивание...' : 'Скачать' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- /Classify Popup -->
  </div>
</template>

<style scoped>
</style>
