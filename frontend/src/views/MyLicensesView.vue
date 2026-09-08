<script setup lang="ts">
import {ref} from 'vue'
import {KeyRound,ArrowUpRight,RefreshCw} from 'lucide-vue-next'
import {api,errorOf} from '../api/client'
import type {Assignment} from '../types'
import {date} from '../utils/format'
import {useResource} from '../utils/useResource'
import ResourceState from '../components/ResourceState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import AppModal from '../components/AppModal.vue'
const rows=ref<Assignment[]>([]),selected=ref<Assignment|null>(null),busy=ref(false),modalError=ref(''),toast=ref('')
const {loading,error,refresh}=useResource(async()=>{rows.value=(await api.get<Assignment[]>('/license-assignments/me')).data})
async function submit(){busy.value=true;modalError.value='';try{await api.post(`/license-assignments/${selected.value!.id}/return`);selected.value=null;toast.value='반납이 완료되었습니다.';setTimeout(()=>toast.value='',4000);await refresh(true)}catch(e){modalError.value=errorOf(e).message}finally{busy.value=false}}
</script>
<template><div class="simple-page-heading"><h1>내 라이선스</h1><div class="heading-actions"><button class="btn" @click="refresh()"><RefreshCw :size="16"/>새로고침</button><RouterLink class="btn" to="/licenses">라이선스 탐색<ArrowUpRight :size="17"/></RouterLink></div></div><div class="section-toolbar"><h2 class="section-title">사용 중인 라이선스 <span>{{rows.length}}</span></h2></div><ResourceState :loading="loading" :error="error" :empty="!rows.length" message="현재 사용 중인 라이선스가 없습니다." @retry="refresh()"><div class="license-grid"><article v-for="row in rows" :key="row.id" class="license-card my-license"><div class="card-top"><div class="product-logo" :data-vendor="row.license.vendor"><KeyRound :size="25"/></div><StatusBadge :status="row.status"/></div><h3>{{row.license.name}}</h3><p class="product-meta">{{row.license.vendor}} · {{row.license.plan_name}}</p><dl><div><dt>권한 승인 시작일</dt><dd>{{date(row.valid_from)}}</dd></div><div><dt>권한 승인 종료일</dt><dd>{{date(row.valid_until)}}</dd></div></dl><p class="my-license-reason">{{row.reason || '관리자가 직접 배정한 라이선스입니다.'}}</p><button class="btn full" @click="selected=row;modalError=''">반납</button></article></div></ResourceState><div v-if="toast" class="toast" role="status">{{toast}}</div><AppModal v-if="selected" title="라이선스를 반납할까요?" :busy="busy" @close="!busy && (selected=null)"><div class="modal-summary"><strong>{{selected.license.name}}</strong><span>권한 승인 기간 {{date(selected.valid_from)}} ~ {{date(selected.valid_until)}}</span></div><p class="notice">반납하면 내 라이선스에서 제거되고 잔여 좌석에 즉시 반영됩니다. 다시 사용하려면 새로 신청해야 합니다.</p><p v-if="modalError" class="notice error" role="alert">{{modalError}}</p><div class="modal-actions"><button class="btn" :disabled="busy" @click="selected=null">계속 사용</button><button class="btn primary" :disabled="busy" @click="submit">{{busy?'처리 중…':'반납 확인'}}</button></div></AppModal></template>
