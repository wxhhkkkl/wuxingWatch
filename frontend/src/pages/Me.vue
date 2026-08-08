<script setup lang="ts">
import { useRouter } from 'vue-router'
import { showSuccessToast } from 'vant'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function onLogout() {
  await auth.logout()
  showSuccessToast('已退出登录')
  router.replace('/')
}
</script>

<template>
  <div class="me-page">
    <van-nav-bar title="我的" />

    <div class="profile">
      <div class="avatar">
        <van-icon name="user-circle-o" size="60" color="#fff" />
      </div>
      <p class="phone">{{ auth.isLoggedIn ? auth.user?.phone : '未登录' }}</p>
      <van-button
        v-if="!auth.isLoggedIn"
        type="primary"
        round
        class="profile-btn"
        @click="router.push('/login')"
      >
        登录 / 注册
      </van-button>
      <van-button v-else round plain class="profile-btn" @click="onLogout">退出登录</van-button>
    </div>

    <van-cell-group inset class="wx-card" style="margin-top: 0">
      <van-cell title="我的记录" icon="todo-list-o" is-link to="/records" />
      <van-cell title="关于五行排盘" icon="info-o" value="v0.1.0" />
    </van-cell-group>
  </div>
</template>

<style scoped>
.profile {
  padding: 32px 16px 28px;
  text-align: center;
  background: linear-gradient(160deg, #a63431, #b85043);
  border-radius: 0 0 22px 22px;
}
.avatar {
  display: inline-flex;
}
.phone {
  color: #fff;
  margin: 10px 0 14px;
  font-size: 15px;
  letter-spacing: 1px;
}
.profile-btn {
  width: 140px;
}
</style>
