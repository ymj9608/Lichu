<script setup lang="ts">
import {computed,ref} from 'vue'
import {useRoute} from 'vue-router'
import {Search,Plus,ArrowRight,Layers as LayersIcon,RefreshCw,Pencil} from 'lucide-vue-next'
import {api,errorOf} from '../api/client'
import type {License,LicenseInput,Assignment} from '../types'
import {useResource} from '../utils/useResource'
import {date,validDates} from '../utils/format'
import LicenseCard from '../components/LicenseCard.vue'
import ResourceState from '../components/ResourceState.vue'
import AppModal from '../components/AppModal.vue'
const route=useRoute(),admin=computed(()=>route.path.startsWith('/admin'))
const licenses=ref<License[]>([]),search=ref(''),category=ref('전체'),toast=ref('')
const {loading,error,refresh}=useResource(async()=>{licenses.value=(await api.get<License[]>(admin.value?'/admin/licenses':'/licenses')).data})
const categories=computed(()=>['전체',...new Set(licenses.value.map(x=>x.category))])
const filtered=computed(()=>licenses.value.filter(l=>(category.value==='전체'||l.category===category.value)&&`${l.name} ${l.vendor}`.toLowerCase().includes(search.value.toLowerCase())))
const mode=ref<'request'|'edit'|'users'|'revoke'|'period'|null>(null),selected=ref<License|null>(null),assignment=ref<Assignment|null>(null),users=ref<Assignment[]>([]),usersLoading=ref(false),usersError=ref(''),busy=ref(false),modalError=ref(''),userSearch=ref('')
const reason=ref(''),start=ref(new Date().toISOString().slice(0,10)),end=ref('')
const blank=():LicenseInput=>({name:'',vendor:'',plan_name:'',category:'개발',description:'',total_seats:1,unit_price:'0',billing_cycle:'MONTHLY',status:'ACTIVE'})
const form=ref<LicenseInput>(blank())
const titles={request:'라이선스 사용 신청',edit:'라이선스 등록 / 수정',users:'라이선스 사용자 관리',revoke:'라이선스 권한 회수',period:'권한 승인 기간 수정'}
const filteredUsers=computed(()=>{const query=userSearch.value.trim().toLowerCase();return query?users.value.filter(item=>`${item.user.name} ${item.user.department.name} ${item.user.job_title} ${item.user.email}`.toLowerCase().includes(query)):users.value})
function close(){if(!busy.value){mode.value=null;modalError.value=''}}
function message(value:string){toast.value=value;setTimeout(()=>toast.value='',4500)}
async function openRequest(lic:License){selected.value=lic;mode.value='request';reason.value='';end.value='';modalError.value='';try{selected.value=(await api.get<License>(`/licenses/${lic.id}`)).data}catch(e){modalError.value=errorOf(e).message}}
function edit(lic:License|null){selected.value=lic;form.value=lic?Object.fromEntries(Object.keys(blank()).map(k=>[k,lic[k as keyof LicenseInput]])) as unknown as LicenseInput:blank();modalError.value='';mode.value='edit'}
async function showUsers(lic:License){selected.value=lic;mode.value='users';modalError.value='';userSearch.value='';usersLoading.value=true;usersError.value='';try{users.value=(await api.get<Assignment[]>(`/admin/licenses/${lic.id}/assignments`)).data}catch(e){usersError.value=errorOf(e).message}finally{usersLoading.value=false}}
function revoke(item:Assignment){assignment.value=item;reason.value='';modalError.value='';mode.value='revoke'}
function editPeriod(item:Assignment){assignment.value=item;start.value=item.valid_from;end.value=item.valid_until;modalError.value='';mode.value='period'}
async function submit(){
  if((mode.value==='request'||mode.value==='period')&&!validDates(start.value,end.value)){modalError.value='시작일은 종료일 이전이어야 합니다.';return}
  busy.value=true;modalError.value=''
  try{
    if(mode.value==='request'){
      await api.post('/license-requests',{license_id:selected.value!.id,reason:reason.value,start_date:start.value,end_date:end.value});message('사용 신청이 완료되었습니다. 내 신청에서 결과를 확인하세요.')
    }else if(mode.value==='edit'){
      if(selected.value)await api.patch(`/admin/licenses/${selected.value.id}`,form.value)
      else await api.post('/admin/licenses',form.value)
      message('라이선스 정보가 저장되었습니다.')
    }else if(mode.value==='revoke'){
      await api.post(`/admin/license-assignments/${assignment.value!.id}/revoke`,{reason:reason.value});message('라이선스를 회수했습니다. 잔여 좌석에 반영되었습니다.')
    }else if(mode.value==='period'){
      await api.patch(`/admin/license-assignments/${assignment.value!.id}`,{valid_from:start.value,valid_until:end.value});message('권한 승인 기간을 수정했습니다.')
    }
    const returnToUsers=mode.value==='revoke'||mode.value==='period';mode.value=null;await refresh(true)
    if(returnToUsers&&selected.value)await showUsers(licenses.value.find(l=>l.id===selected.value!.id) || selected.value)
  }catch(e){const err=errorOf(e);modalError.value=[err.message,...Object.values(err.fields || {})].join(' ');await refresh(true)}finally{busy.value=false}
}
</script>
<template><div v-if="admin" class="simple-page-heading"><h1>라이선스 관리</h1></div><div v-else class="page-heading"><div><span class="eyebrow">EXPLORE YOUR POSSIBILITIES</span><h1>좋은 도구가, 좋은 일을 만듭니다.</h1><p>필요한 소프트웨어를 찾아보세요. 더 나은 업무의 시작을 함께합니다.</p></div><span class="page-stamp">YOUR NEXT GREAT IDEA<br><b>STARTS HERE ↗</b></span></div>
<div v-if="!admin" class="catalog-banner"><div class="banner-icon"><LayersIcon/></div><div><strong>우리 팀의 도구, 한눈에 확인하세요</strong><p>좌석 확인부터 사용 신청까지. 승인 결과는 내 신청에서 확인할 수 있어요.</p></div><RouterLink to="/requests">내 신청 보기<ArrowRight :size="16"/></RouterLink></div>
<div class="catalog-toolbar"><div class="category-tabs"><button v-for="cat in categories" :key="cat" :class="{active:category===cat}" @click="category=cat">{{cat}}<span v-if="cat==='전체'">{{licenses.length}}</span></button></div><div class="search-field"><Search :size="17"/><input v-model="search" aria-label="라이선스 검색" placeholder="소프트웨어 또는 공급사 검색"></div></div>
<div class="list-caption"><span>총 <b>{{filtered.length}}</b>개의 라이선스</span><div class="list-actions"><button class="btn" aria-label="새로고침" @click="refresh()"><RefreshCw :size="16"/>새로고침</button><button v-if="admin" class="btn primary" @click="edit(null)"><Plus :size="17"/>라이선스 등록</button></div></div>
<ResourceState :loading="loading" :error="error" :empty="!filtered.length" message="조건에 맞는 라이선스가 없습니다." @retry="refresh()"><div class="license-grid"><LicenseCard v-for="lic in filtered" :key="lic.id" :license="lic" :admin="admin" @request="openRequest" @users="showUsers" @edit="edit"/></div></ResourceState>
<div v-if="toast" class="toast" role="status">{{toast}}</div>
<AppModal v-if="mode" :title="titles[mode]" :wide="mode==='users'||mode==='edit'" :busy="busy" @close="close"><div v-if="selected" class="modal-summary"><strong>{{selected.name}}</strong><span>{{selected.vendor}} · 사용 {{selected.used_seats}} / {{selected.total_seats}}석 · 잔여 {{selected.available_seats}}석</span></div>
<template v-if="mode==='users'"><div class="user-search"><Search :size="17"/><input v-model="userSearch" aria-label="직원 검색" placeholder="이름, 부서, 직급 또는 이메일 검색"></div><ResourceState :loading="usersLoading" :error="usersError" :empty="!filteredUsers.length" :message="users.length?'검색 결과가 없습니다.':'현재 할당된 사용자가 없습니다.'" @retry="selected && showUsers(selected)"><div class="assignment-list"><div class="assignment-user" v-for="item in filteredUsers" :key="item.id"><div class="user-avatar" :class="{default:!item.user.profile_image}"><img :src="item.user.profile_image || '/default-profile.svg'" :alt="item.user.profile_image?`${item.user.name} 프로필`:'기본 프로필'"></div><div class="assignment-user-info"><strong>{{item.user.name}}</strong><p>{{item.user.department.name}} · {{item.user.job_title}}</p><p>{{item.user.email}}</p><p>권한 승인 기간 {{date(item.valid_from)}} ~ {{date(item.valid_until)}}</p></div><div class="assignment-actions"><button class="btn compact" @click="editPeriod(item)"><Pencil :size="14"/>수정</button><button class="btn danger compact" @click="revoke(item)">권한 회수</button></div></div></div></ResourceState></template>
<form v-else @submit.prevent="submit"><template v-if="mode==='edit'"><div class="form-grid"><label>라이선스 이름<input v-model="form.name" required maxlength="150"></label><label>공급사<input v-model="form.vendor" required maxlength="100"></label><label>플랜<input v-model="form.plan_name" required maxlength="100"></label><label>카테고리<input v-model="form.category" list="category-options" required maxlength="50"><datalist id="category-options"><option>개발</option><option>디자인</option><option>생산성</option></datalist></label><label class="span2">설명<textarea v-model="form.description" required maxlength="4000"></textarea></label><label>총 좌석<input v-model.number="form.total_seats" type="number" min="0" max="1000000" required></label><label>사용자당 단가 (USD)<input v-model="form.unit_price" type="number" min="0" step="0.01" required></label><label>청구 주기<select v-model="form.billing_cycle"><option value="MONTHLY">월간</option><option value="YEARLY">연간</option></select></label><label>운영 상태<select v-model="form.status"><option value="ACTIVE">활성</option><option value="INACTIVE">비활성</option></select></label></div><p class="form-hint">사용 중인 좌석보다 작게 설정할 수 없습니다. 비활성화해도 기존 할당과 이력은 유지됩니다.</p></template>
<template v-else><div v-if="(mode==='revoke'||mode==='period') && assignment" class="notice"><b>{{assignment.user.name}}</b> · {{assignment.user.department.name}}<br>권한 승인 기간 {{date(assignment.valid_from)}} ~ {{date(assignment.valid_until)}}</div><template v-if="mode==='period'"><div class="form-grid"><label>권한 승인 시작일<input v-model="start" type="date" required></label><label>권한 승인 종료일<input v-model="end" type="date" :min="start" required></label></div></template><template v-else><label>{{mode==='request'?'사용 목적':'회수 사유'}} <span class="required">*</span><textarea v-model="reason" required maxlength="4000" :placeholder="mode==='request'?'어떤 업무나 프로젝트에 필요한지 알려주세요.':'회수 사유를 입력해주세요.'"></textarea></label><div v-if="mode==='request'" class="form-grid"><label>사용 시작 예정일<input v-model="start" type="date" required></label><label>사용 종료 예정일<input v-model="end" type="date" :min="start" required></label></div></template></template>
<p v-if="modalError" class="notice error" role="alert">{{modalError}}</p><div class="modal-actions"><button type="button" class="btn" :disabled="busy" @click="close">취소</button><button class="btn" :class="mode==='revoke'?'danger-solid':'primary'" :disabled="busy || (mode==='request' && Boolean(selected?.request_block))">{{busy?'처리 중…':mode==='edit'||mode==='period'?'저장':mode==='revoke'?'권한 회수':'신청하기'}}</button></div></form></AppModal></template>
