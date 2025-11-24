<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

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

    classifyStatus.value = { type: 'success', message: responseData?.message || 'Файл отправлен в бакет raw' }
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
        <div class="main-block">
          <p>
            Какой-то текст для тела нашего проекта
          </p>
        </div>
      </div>
    </main>

    <footer>
      <div class="wrapper footer-box">
        <div class="footer-block">
          <p class="footer-title">Разработчики</p>
          <br>
          <p>Команда 11</p>
        </div>
        <div class="footer-block">
          <p class="footer-title">Источники</p>
          <br>
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
          </div>
        </div>
      </div>
    </div>
    <!-- /Classify Popup -->
  </div>
</template>

<style scoped>
</style>
