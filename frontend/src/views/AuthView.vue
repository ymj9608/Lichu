<script setup lang="ts">
import {computed,ref,onMounted} from 'vue'
import {useRoute,useRouter} from 'vue-router'
import {ArrowRight,Check,LoaderCircle,KeyRound,UserRound,Camera} from 'lucide-vue-next'
import {api,errorOf} from '../api/client'
import {useAuth} from '../stores/auth'
import type {Department} from '../types'
import AppModal from '../components/AppModal.vue'

const route=useRoute(),router=useRouter(),auth=useAuth()
const signup=computed(()=>route.path==='/signup')
const busy=ref(false),error=ref(''),fieldErrors=ref<Record<string,string>>({}),departments=ref<Department[]>([])
const remember=ref(false),help=ref<'id'|'password'|null>(null)
const form=ref({employee_no:'',name:'',department_id:0,job_title:'',email:'',username:'',password:'',password_confirm:'',profile_image:null as string|null})
const labels:Record<string,string>={employee_no:'사번',name:'이름',department_id:'부서',job_title:'직급 / 직책',email:'회사 이메일',username:'아이디',password:'비밀번호',password_confirm:'비밀번호 확인'}
const signupKeys=['employee_no','name','department_id','job_title','email','username','password','password_confirm'] as const

async function loadDepartments(){try{departments.value=(await api.get<Department[]>('/departments')).data;error.value=''}catch(e){error.value=errorOf(e).message}}
onMounted(()=>{
  void loadDepartments()
  const saved=localStorage.getItem('lichu_saved_username')
  if(saved){form.value.username=saved;remember.value=true}
})
function selectImage(event:Event){
  const input=event.target as HTMLInputElement,file=input.files?.[0]
  if(!file)return
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)){fieldErrors.value.profile_image='JPG, PNG, WEBP 이미지만 등록할 수 있습니다.';input.value='';return}
  const reader=new FileReader()
  reader.onload=()=>{form.value.profile_image=String(reader.result);delete fieldErrors.value.profile_image}
  reader.readAsDataURL(file)
}
async function submit(){
  busy.value=true;error.value='';fieldErrors.value={}
  try{
    if(signup.value){await api.post('/auth/signup',form.value);form.value.password='';form.value.password_confirm='';await router.push('/login?registered=1')}
    else{
      await auth.login(form.value.username,form.value.password)
      if(remember.value)localStorage.setItem('lichu_saved_username',form.value.username)
      else localStorage.removeItem('lichu_saved_username')
      await router.push(auth.user?.role==='MASTER'?'/admin':'/licenses')
    }
  }catch(e){const err=errorOf(e);error.value=err.message;fieldErrors.value=err.fields||{}}
  finally{busy.value=false}
}
</script>

<template><div class="auth-page">
  <section class="auth-story">
    <a href="/" class="brand"><span class="brand-icon">L<span>•</span></span>LiChU<span class="brand-period">.</span></a>
    <div class="auth-visual-dots"><i></i><i></i><i></i></div>
    <div class="story-content">
      <h1>사내 SaaS 라이선스를<br><span>한곳에서 신청하고 관리하세요.</span></h1>
      <p>잔여 라이선스 확인부터 신청, 승인, 반납과 회수까지<br>하나의 흐름으로 관리합니다.</p>
      <div class="mascot-stage"><div class="mascot-orbit"></div><img src="/lichu-mascot.png" alt="LiChU. 프로젝트 마스코트"><span class="floating-label"><Check :size="15"/> License workflow ready</span></div>
      <div class="story-features"><span><Check :size="16"/> 한눈에 보는 잔여 라이선스 현황</span><span><Check :size="16"/> 간편한 신청과 승인</span></div>
    </div>
  </section>
  <section class="auth-form-area">
    <div class="auth-form-decoration"><span></span><span></span><span></span></div>
    <div class="auth-form">
      <div class="auth-tabs"><RouterLink to="/login" :class="{active:!signup}" @click="error='';fieldErrors={}">로그인</RouterLink><RouterLink to="/signup" :class="{active:signup}" @click="error='';fieldErrors={}">회원가입</RouterLink></div>
      <p v-if="route.query.registered" class="notice success" role="status">회원가입이 완료되었습니다. 로그인해주세요.</p>
      <p v-if="route.query.expired" class="notice">로그인 시간이 만료되었습니다. 다시 로그인해주세요.</p>
      <div v-if="error" class="notice error" role="alert">{{error}}<button v-if="!departments.length&&signup" class="text-button" @click="loadDepartments">부서 목록 다시 불러오기</button></div>
      <form @submit.prevent="submit">
        <div v-if="signup" class="profile-upload auth-profile-upload">
          <div class="profile-preview"><img :src="form.profile_image || '/default-profile.svg'" :alt="form.profile_image?'프로필 미리보기':'기본 프로필'"></div>
          <label class="btn compact"><Camera :size="15"/>프로필 사진 등록<input class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" @change="selectImage"></label>
          <span>선택하지 않으면 기본 프로필로 등록됩니다.</span><small v-if="fieldErrors.profile_image" class="field-error">{{fieldErrors.profile_image}}</small>
        </div>
        <div v-if="signup" class="form-grid"><label v-for="key in signupKeys" :key="key" :class="{span2:key==='email'}">{{labels[key]}} <span class="required">*</span><select v-if="key==='department_id'" v-model="form.department_id" required><option :value="0" disabled>부서 선택</option><option v-for="dep in departments" :key="dep.id" :value="dep.id">{{dep.name}}</option></select><input v-else v-model="form[key]" :type="key.includes('password')?'password':key==='email'?'email':'text'" :autocomplete="key.includes('password')?'new-password':key==='username'?'username':'off'" :minlength="key==='password'?8:key==='username'?4:undefined" :placeholder="key==='password'?'8자 이상':labels[key]+' 입력'" required :aria-invalid="Boolean(fieldErrors[key])"><span class="field-error" v-if="fieldErrors[key]">{{fieldErrors[key]}}</span></label></div>
        <template v-else>
          <label>아이디<input v-model="form.username" autocomplete="username" placeholder="아이디를 입력해주세요" required></label>
          <label>비밀번호<input v-model="form.password" type="password" autocomplete="current-password" placeholder="비밀번호를 입력해주세요" required></label>
          <div class="login-options"><label class="check-label"><input v-model="remember" type="checkbox">로그인 정보 저장</label><div><button type="button" @click="help='id'">ID 찾기</button><span></span><button type="button" @click="help='password'">비밀번호 찾기</button></div></div>
        </template>
        <button class="btn primary full auth-submit" :disabled="busy"><LoaderCircle v-if="busy" class="spin" :size="18"/>{{busy?'처리 중…':signup?'회원가입':'로그인'}}<ArrowRight :size="18"/></button>
      </form>
    </div>
  </section>
  <AppModal v-if="help" :title="help==='id'?'ID 찾기':'비밀번호 찾기'" @close="help=null"><div class="account-help"><component :is="help==='id'?UserRound:KeyRound" :size="28"/><p>사내 계정 정보 확인이 필요합니다.</p><span>이름, 사번, 회사 이메일을 준비해 IT 자산관리팀에 문의해주세요.</span></div><div class="modal-actions"><button class="btn primary" @click="help=null">확인</button></div></AppModal>
</div></template>
