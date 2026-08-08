<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 仅主 Tab 页显示底部导航
const TAB_NAMES = ['home', 'records', 'me']
const showTabbar = computed(() => TAB_NAMES.includes(String(route.name)))
</script>

<template>
  <div class="app-shell">
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>

    <van-tabbar v-if="showTabbar" route safe-area-inset-bottom>
      <van-tabbar-item replace to="/" icon="chart-trending-o">排盘</van-tabbar-item>
      <van-tabbar-item replace to="/records" icon="todo-list-o">记录</van-tabbar-item>
      <van-tabbar-item replace to="/me" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
