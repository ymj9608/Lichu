<script setup lang="ts">
import {computed,ref} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {LayoutGrid,ClipboardList,KeyRound,ChartNoAxesCombined,Layers,LogOut,ChevronRight,ShieldCheck,Camera} from 'lucide-vue-next'
import {useAuth} from '../stores/auth'
import {api,errorOf} from '../api/client'
import type {Department} from '../types'
import AppModal from '../components/AppModal.vue'

const auth=useAuth(),route=useRoute(),router=useRouter()
const admin=computed(()=>auth.user?.role==='MASTER')
const links=computed(()=>admin.value?[
  {to:'/admin',label:'대시보드',icon:ChartNoAxesCombined},{to:'/admin/requests',label:'신청 관리',icon:ClipboardList},{to:'/admin/licenses',label:'라이선스 관리',icon:Layers}]:[
  {to:'/licenses',label:'라이선스 탐색',icon:LayoutGrid},{to:'/requests',label:'내 신청',icon:ClipboardList},{to:'/my-licenses',label:'내 라이선스',icon:KeyRound}])
const profileOpen=ref(false),departments=ref<Department[]>([]),busy=ref(false),profileError=ref('')
const profile=ref({name:'',department_id:0,job_title:'',email:'',profile_image:null as string|null})
function logout(){auth.logout();void router.push('/login')}
async function openProfile(){
  if(!auth.user)return
  profile.value={name:auth.user.name,department_id:auth.user.department_id,job_title:auth.user.job_title,email:auth.user.email,profile_image:auth.user.profile_image}
  profileError.value='';profileOpen.value=true
  try{departments.value=(await api.get<Department[]>('/departments')).data}catch(e){profileError.value=errorOf(e).message}
}
function selectImage(event:Event){
  const input=event.target as HTMLInputElement,file=input.files?.[0]
  if(!file)return
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)){profileError.value='JPG, PNG, WEBP 이미지만 등록할 수 있습니다.';return}
  const reader=new FileReader();reader.onload=()=>{profile.value.profile_image=String(reader.result);profileError.value=''};reader.readAsDataURL(file)
}
async function saveProfile(){
  busy.value=true;profileError.value=''
  try{await api.patch('/auth/me',profile.value);await auth.me();profileOpen.value=false}catch(e){profileError.value=errorOf(e).message}finally{busy.value=false}
}
</script>

<template><div class="app-shell">
  <aside class="sidebar" :class="{'admin-sidebar':admin}"><RouterLink :to="admin?'/admin':'/licenses'" class="brand"><img class="brand-logo" src="/logo.png" alt="LiChU 로고">LiChU<span class="brand-period">.</span></RouterLink><p class="nav-caption">{{admin?'ADMIN WORKSPACE':'MY WORKSPACE'}}</p><nav><RouterLink v-for="link in links" :key="link.to" :to="link.to" :class="{selected:route.path===link.to}"><component :is="link.icon" :size="19"/><span>{{link.label}}</span><ChevronRight v-if="route.path===link.to" :size="15"/></RouterLink></nav><div class="sidebar-bottom"><button class="logout" @click="logout"><LogOut :size="17"/>로그아웃</button><small>© 2026 LiChU. All rights reserved.</small></div></aside>
  <div class="main-shell"><header class="topbar"><div class="breadcrumb">워크스페이스 <ChevronRight :size="14"/><span>{{route.meta.title}}</span></div><button class="topbar-user" aria-label="회원 정보 수정" @click="openProfile"><span class="role-label"><ShieldCheck :size="14"/>{{admin?'관리자':'임직원'}}</span><div class="user-avatar" :class="{default:!auth.user?.profile_image}"><img :src="auth.user?.profile_image || '/default-profile.svg'" :alt="auth.user?.profile_image?`${auth.user?.name} 프로필`:'기본 프로필'"></div><div><strong>{{auth.user?.name}}</strong><small>{{auth.user?.department.name}} · {{auth.user?.job_title}}</small></div></button></header><main id="main-content"><RouterView/></main><footer class="main-footer"><span>© 2026 LiChU. All rights reserved.</span><span>Internal SaaS License Management System</span></footer></div>
  <AppModal v-if="profileOpen" title="회원 정보 수정" :busy="busy" @close="profileOpen=false"><form @submit.prevent="saveProfile"><div class="profile-upload"><div class="profile-preview"><img :src="profile.profile_image || '/default-profile.svg'" :alt="profile.profile_image?'프로필 미리보기':'기본 프로필'"></div><div><label class="btn compact"><Camera :size="15"/>프로필 사진 변경<input class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" @change="selectImage"></label><button v-if="profile.profile_image" type="button" class="text-button profile-remove" @click="profile.profile_image=null">기본 프로필 사용</button></div></div><div class="profile-fixed"><span>사번 {{auth.user?.employee_no}}</span><span>아이디 {{auth.user?.username}}</span></div><div class="form-grid"><label>이름<input v-model="profile.name" required maxlength="100"></label><label>부서<select v-model="profile.department_id" required><option v-for="dep in departments" :key="dep.id" :value="dep.id">{{dep.name}}</option></select></label><label>직급 / 직책<input v-model="profile.job_title" required maxlength="100"></label><label>회사 이메일<input v-model="profile.email" type="email" required maxlength="255"></label></div><p v-if="profileError" class="notice error" role="alert">{{profileError}}</p><div class="modal-actions"><button type="button" class="btn" :disabled="busy" @click="profileOpen=false">취소</button><button class="btn primary" :disabled="busy">{{busy?'저장 중…':'저장'}}</button></div></form></AppModal>
</div></template>
