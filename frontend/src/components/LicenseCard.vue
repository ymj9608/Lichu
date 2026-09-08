<script setup lang="ts">
import {ArrowUpRight,ArrowRight,TriangleAlert,Pencil} from 'lucide-vue-next'
import type {License} from '../types'
import {money,requestLabel} from '../utils/format'
import StatusBadge from './StatusBadge.vue'
defineProps<{license:License;admin?:boolean}>()
defineEmits<{request:[license:License];users:[license:License];edit:[license:License]}>()
const symbols:Record<string,string>={GitHub:'GH',Figma:'F',JetBrains:'IJ',Adobe:'Ad',Notion:'N',Slack:'S'}
</script>
<template><article class="license-card" :class="{clickable:admin}" :tabindex="admin?0:undefined" :role="admin?'button':undefined" :aria-label="admin?`${license.name} 사용자 보기`:undefined" @click="admin && $emit('users',license)" @keydown.enter.self="admin && $emit('users',license)">
  <div class="card-top"><div class="product-logo" :data-vendor="license.vendor">{{symbols[license.vendor] || license.vendor.slice(0,2)}}</div><span class="category-label">{{license.category}}</span><button v-if="admin" class="icon-button edit-button" :aria-label="`${license.name} 수정`" @click.stop="$emit('edit',license)"><Pencil :size="16"/></button></div>
  <h3>{{license.name}}</h3><div class="product-meta">{{license.vendor}} <span>·</span> {{license.plan_name}}</div><p class="product-description">{{license.description}}</p>
  <div class="price"><strong>{{money(license.unit_price)}}</strong><span>/ 사용자 · {{license.billing_cycle==='MONTHLY'?'월':'년'}}</span><span v-if="license.billing_cycle==='YEARLY'">(월 {{money(license.monthly_unit_price)}})</span></div>
  <div class="usage-line"><span>좌석 사용 현황</span><span><b>{{license.used_seats}}</b> / {{license.total_seats}}석</span></div><div class="progress" :class="{warning:license.utilization>=90}"><span :style="{width:`${license.utilization}%`}"></span></div>
  <div class="seat-line"><span :class="license.available_seats>0?'text-success':'text-warning'">{{license.available_seats>0?`${license.available_seats}석 신청 가능`:'잔여 좌석 없음'}}</span><span class="text-warning" v-if="license.utilization>=90"><TriangleAlert :size="12"/> {{license.utilization}}% 사용</span><span v-else>{{license.utilization}}% 사용</span></div>
  <div class="card-footer"><StatusBadge :status="license.status"/><button v-if="admin" class="text-button" @click.stop="$emit('users',license)">사용자 관리 <ArrowUpRight :size="16"/></button><button v-else class="btn primary compact" :disabled="Boolean(license.request_block)" @click="$emit('request',license)">{{requestLabel(license.request_block)}}<ArrowRight v-if="!license.request_block" :size="15"/></button></div>
</article></template>
