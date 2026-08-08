<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const phone = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!phone.value || !password.value) {
    ElMessage.warning('请输入手机号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(phone.value, password.value)
    ElMessage.success('登录成功')
    router.replace('/')
  } catch (e) {
    ElMessage.error((e as Error).message)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 class="title">五行排盘 · 后台管理</h2>
      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="手机号">
          <el-input v-model="phone" placeholder="管理员手机号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            show-password
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button type="primary" style="width: 100%" :loading="loading" @click="onSubmit">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f6f8;
}
.login-card {
  width: 380px;
  padding: 8px 12px;
}
.title {
  text-align: center;
  color: #a63431;
  margin: 0 0 20px;
}
</style>
