<script setup lang="ts">
defineProps<{status:string}>()
const labels:Record<string,string>={PENDING:'승인 대기',APPROVED:'승인 완료',REJECTED:'반려',CANCELED:'취소',ACTIVE:'활성',INACTIVE:'비활성',RETURNED:'반납',REVOKED:'회수'}
</script>
<template><span class="badge" :class="status.toLowerCase()"><span class="status-dot"></span>{{labels[status] || status}}</span></template>
