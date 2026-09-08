<script setup lang="ts">
import {AlertCircle,LoaderCircle,Inbox} from 'lucide-vue-next'
defineProps<{loading?:boolean;error?:string;empty?:boolean;message?:string}>()
defineEmits<{retry:[]}>()
</script>
<template>
  <div v-if="loading" class="state-panel" role="status"><LoaderCircle class="spin" :size="28"/><p>데이터를 불러오고 있습니다.</p></div>
  <div v-else-if="error" class="state-panel error-panel" role="alert"><AlertCircle :size="28"/><p>{{error}}</p><button class="btn" @click="$emit('retry')">다시 시도</button></div>
  <div v-else-if="empty" class="state-panel"><Inbox :size="36"/><h3>{{message || '표시할 데이터가 없습니다.'}}</h3><p>새로운 소식이 생기면 이곳에서 확인할 수 있어요.</p></div>
  <slot v-else/>
</template>
