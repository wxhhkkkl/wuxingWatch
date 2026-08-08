<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const phone = ref('')
const code = ref('')
const sending = ref(false)
const countdown = ref(0)
let timer: number | undefined

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})

function startCountdown() {
  countdown.value = 60
  timer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0 && timer) window.clearInterval(timer)
  }, 1000)
}

async function onSend() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    showToast('请输入有效的手机号')
    return
  }
  sending.value = true
  try {
    await auth.sendCode(phone.value)
    startCountdown()
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    sending.value = false
  }
}

async function onLogin() {
  if (!code.value) {
    showToast('请输入验证码')
    return
  }
  try {
    await auth.login(phone.value, code.value)
    showToast('登录成功')
    router.replace('/')
  } catch (e) {
    showToast((e as Error).message)
  }
}
</script>

<template>
  <div class="login-page">
    <header class="login-hero">
      <h1>五行 · 八字排盘</h1>
      <p>手机号登录，保存你的命盘</p>
    </header>

    <div class="wx-card">
      <p class="wx-card-title">登录 / 注册</p>
      <van-cell-group :border="false">
        <van-field
          v-model="phone"
          type="tel"
          label="手机号"
          placeholder="11 位手机号"
          maxlength="11"
        />
        <van-field v-model="code" label="验证码" placeholder="6 位验证码" maxlength="6">
          <template #button>
            <van-button size="small" :disabled="countdown > 0" :loading="sending" @click="onSend">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </van-button>
          </template>
        </van-field>
      </van-cell-group>

      <div class="submit">
        <van-button type="primary" class="wx-btn-primary" block @click="onLogin">
          登录 / 注册
        </van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
}
.login-hero {
  background: linear-gradient(160deg, #a63431, #b85043);
  color: #fff;
  text-align: center;
  padding: 40px 20px 30px;
  border-radius: 0 0 22px 22px;
}
.login-hero h1 {
  margin: 0;
  font-size: 22px;
  letter-spacing: 3px;
  font-family: Georgia, "Songti SC", "STSong", "SimSun", serif;
}
.login-hero p {
  margin: 8px 0 0;
  font-size: 13px;
  opacity: 0.85;
}
.submit {
  margin-top: 18px;
}
</style>
