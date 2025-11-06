<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const isAuthOpen = ref(false)

function openAuth() {
  isAuthOpen.value = true
}

function closeAuth() {
  isAuthOpen.value = false
}

function onKeydown(e) {
  if (e.key === 'Escape') closeAuth()
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
          <a href="#" class="header-button" @click.prevent="openAuth">Войти как администратор</a>
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
            <a href="#" class="banner-button">Классифицировать</a>
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
          111
        </div>
        <div class="footer-block">
          222
        </div>
        <div class="footer-block">
          333
        </div>
      </div>
    </footer>

    <!-- Auth Popup -->
    <div v-if="isAuthOpen" class="modal-overlay" @click.self="closeAuth">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Авторизация</div>
          <button class="modal-close" @click="closeAuth" aria-label="Закрыть">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent>
            <label class="form-label" for="login">Логин</label>
            <input id="login" type="text" class="form-input" placeholder="Введите логин" autocomplete="username" />

            <label class="form-label" for="password">Пароль</label>
            <input id="password" type="password" class="form-input" placeholder="Введите пароль" autocomplete="current-password" />

            <div class="modal-actions">
              <button type="submit" class="popup-button">Войти</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- /Auth Popup -->
  </div>
</template>

<style scoped>
</style>
