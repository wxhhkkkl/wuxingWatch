<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function onLogout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <el-container v-if="route.name !== 'login'" class="layout">
    <el-aside width="200px" class="aside">
      <div class="logo">五行排盘 · 后台管理</div>
      <el-menu router :default-active="route.path" class="menu">
        <el-menu-item index="/">会员管理</el-menu-item>
        <el-menu-item index="/books">书籍管理</el-menu-item>
        <el-menu-item index="/categories">分类管理</el-menu-item>
      </el-menu>
      <div class="aside-footer">
        <span class="phone">{{ auth.user?.phone }}</span>
        <el-button size="small" text type="primary" @click="onLogout">退出</el-button>
      </div>
    </el-aside>
    <el-main class="main">
      <router-view :key="route.path" />
    </el-main>
  </el-container>
  <router-view v-else />
</template>

<style>
body {
  margin: 0;
  background: #f5f7fa;
}
.layout {
  height: 100vh;
}
.aside {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #e4e7ed;
}
.logo {
  padding: 18px 16px;
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
}
.menu {
  flex: 1;
  border-right: none;
}
.aside-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #909399;
}
.main {
  padding: 16px;
  overflow: auto;
}
</style>
