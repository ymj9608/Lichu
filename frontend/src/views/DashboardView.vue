<script setup lang="ts">
import {ref} from 'vue'
import {Layers,KeyRound,Clock3,CheckCircle2,ArrowUpRight,RefreshCw} from 'lucide-vue-next'
import {api} from '../api/client'
import type {Dashboard} from '../types'
import {useResource} from '../utils/useResource'
import ResourceState from '../components/ResourceState.vue'
const data=ref<Dashboard|null>(null)
const {loading,error,refresh}=useResource(async()=>{data.value=(await api.get<Dashboard>('/admin/dashboard')).data})
const metrics=[{key:'total_seats',label:'전체 라이선스 좌석',icon:Layers},{key:'used_seats',label:'사용 중인 좌석',icon:KeyRound},{key:'available_seats',label:'잔여 좌석',icon:CheckCircle2},{key:'pending_requests',label:'승인 대기 요청',icon:Clock3}] as const
</script>

<template><div class="simple-page-heading"><h1>대시보드</h1><button class="btn" @click="refresh()"><RefreshCw :size="16"/>새로고침</button></div>
<ResourceState :loading="loading" :error="error" @retry="refresh()"><template v-if="data">
  <div class="stats-grid"><article v-for="(metric,i) in metrics" :key="metric.key" class="stat-card" :class="{accent:i===3}"><div class="stat-heading"><span>{{metric.label}}</span><component :is="metric.icon" :size="20"/></div><strong>{{data[metric.key]}}<small>{{i===3?'건':'석'}}</small></strong></article></div>
  <div class="dashboard-columns dashboard-balanced">
    <section class="panel dashboard-panel"><div class="panel-heading"><h2>라이선스별 사용 현황</h2><RouterLink to="/admin/licenses" class="text-button">전체 보기<ArrowUpRight :size="16"/></RouterLink></div><div class="dashboard-scroll"><div class="usage-row" v-for="lic in data.licenses" :key="lic.id"><div class="usage-title"><div class="mini-logo" :data-vendor="lic.vendor">{{lic.vendor.slice(0,2)}}</div><div><strong>{{lic.name}}</strong><small>{{lic.plan_name}}</small></div><span><b>{{lic.used_seats}}</b> / {{lic.total_seats}}석</span></div><div class="usage-meter"><div class="progress" :class="{warning:lic.utilization>=90}"><span :style="{width:`${lic.utilization}%`}"></span></div><span>{{lic.utilization}}%</span></div></div><p v-if="!data.licenses.length" class="empty-inline">등록된 라이선스가 없습니다.</p></div></section>
    <section class="panel dashboard-panel"><div class="panel-heading"><h2>승인 대기 중 <span class="count-pill">{{data.pending_requests}}</span></h2><RouterLink to="/admin/requests" class="text-button">신청 관리<ArrowUpRight :size="16"/></RouterLink></div><div class="dashboard-scroll"><RouterLink v-for="row in data.recent_requests" :key="row.id" to="/admin/requests" class="recent-row"><div class="user-avatar" :class="{default:!row.user.profile_image}"><img :src="row.user.profile_image || '/default-profile.svg'" :alt="row.user.profile_image?`${row.user.name} 프로필`:'기본 프로필'"></div><div><strong>{{row.user.name}}<small>{{row.user.department.name}}</small></strong><p>{{row.license.name}}</p><small class="request-purpose">{{row.reason}}</small></div><ArrowUpRight :size="16"/></RouterLink><p v-if="!data.recent_requests.length" class="empty-inline">현재 승인 대기 중인 요청이 없습니다.</p></div></section>
  </div>
</template></ResourceState></template>
