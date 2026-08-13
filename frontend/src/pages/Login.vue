<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// 登录成功后回跳的页面（路由守卫传入 redirect），默认首页
const redirect = computed(() =>
  typeof route.query.redirect === 'string' ? route.query.redirect : '/',
)

const tab = ref<'sms' | 'password'>('password')
// 密码登录页内的子模式
const pwMode = ref<'login' | 'register' | 'reset'>('login')

const phone = ref('')
const code = ref('')
const password = ref('')
const sending = ref(false)
const loading = ref(false)
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

function currentIntent(): 'login' | 'register' | 'reset' {
  if (tab.value === 'sms') return 'login'
  return pwMode.value
}

async function onSend() {
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    showToast('请输入有效的手机号')
    return
  }
  sending.value = true
  try {
    await auth.sendCode(phone.value, currentIntent())
    startCountdown()
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    sending.value = false
  }
}

async function onSmsLogin() {
  if (!code.value) {
    showToast('请输入验证码')
    return
  }
  loading.value = true
  try {
    await auth.login(phone.value, code.value)
    showToast('登录成功')
    router.replace(redirect.value)
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function onPasswordSubmit() {
  if (!phone.value || !password.value) {
    showToast('请输入手机号和密码')
    return
  }
  loading.value = true
  try {
    if (pwMode.value === 'login') {
      await auth.loginPassword(phone.value, password.value)
      showToast('登录成功')
      router.replace(redirect.value)
    } else if (pwMode.value === 'register') {
      await auth.register(phone.value, code.value, password.value)
      showToast('注册成功')
      router.replace(redirect.value)
    } else {
      await auth.resetPassword(phone.value, code.value, password.value)
      showToast('密码已重置，请登录')
      pwMode.value = 'login'
      password.value = ''
    }
  } catch (e) {
    showToast((e as Error).message)
  } finally {
    loading.value = false
  }
}

const pwTitle = { login: '密码登录', register: '注册（短信设置密码）', reset: '重置密码' } as const
</script>

<template>
  <div class="login-page">
    <header class="login-hero">
      <h1>五行 · 八字排盘</h1>
      <p>手机号登录，保存你的命盘</p>
    </header>

    <div class="wx-card">
      <van-tabs v-model:active="tab" color="#a63431" title-active-color="#a63431">
        <van-tab title="短信登录" name="sms">
          <van-cell-group :border="false" class="pw-form">
            <van-field v-model="phone" type="tel" label="手机号" placeholder="11 位手机号" maxlength="11" />
            <van-field v-model="code" label="验证码" placeholder="6 位验证码" maxlength="6">
              <template #button>
                <van-button size="small" :disabled="countdown > 0" :loading="sending" @click="onSend">
                  {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
                </van-button>
              </template>
            </van-field>
          </van-cell-group>
          <div class="submit">
            <van-button
              type="primary"
              class="wx-btn-primary"
              block
              data-testid="sms-login-btn"
              :loading="loading"
              @click="onSmsLogin"
            >
              登录 / 注册
            </van-button>
          </div>
        </van-tab>

        <van-tab title="密码登录" name="password">
          <van-cell-group :border="false" class="pw-form">
            <van-field v-model="phone" type="tel" label="手机号" placeholder="11 位手机号" maxlength="11" />
            <van-field
              v-if="pwMode !== 'login'"
              v-model="code"
              label="验证码"
              placeholder="6 位验证码"
              maxlength="6"
            >
              <template #button>
                <van-button size="small" :disabled="countdown > 0" :loading="sending" @click="onSend">
                  {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
                </van-button>
              </template>
            </van-field>
            <van-field v-model="password" type="password" label="密码" placeholder="至少 8 位" />
          </van-cell-group>

          <div class="pw-links">
            <span
              v-if="pwMode !== 'register'"
              class="link"
              @click="pwMode = 'register'; password = ''"
            >
              注册
            </span>
            <span
              v-if="pwMode !== 'reset'"
              class="link"
              @click="pwMode = 'reset'; password = ''"
            >
              忘记密码
            </span>
            <span
              v-if="pwMode !== 'login'"
              class="link"
              @click="pwMode = 'login'; password = ''"
            >
              返回登录
            </span>
          </div>

          <div class="submit">
            <van-button
              type="primary"
              class="wx-btn-primary"
              block
              data-testid="pw-login-btn"
              :loading="loading"
              @click="onPasswordSubmit"
            >
              {{ pwTitle[pwMode] }}
            </van-button>
          </div>
        </van-tab>
      </van-tabs>
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
.pw-form {
  margin-top: 8px;
}
.submit {
  margin: 18px 0 4px;
}
.pw-links {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 8px 4px 0;
}
.link {
  color: #a63431;
  font-size: 13px;
}
</style>
