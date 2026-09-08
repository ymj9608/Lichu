import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'
import type {User} from '../types'
export const useAuth = defineStore('auth',()=>{
  const user = ref<User|null>(null)
  async function me(){user.value = (await api.get<User>('/auth/me')).data}
  async function login(username:string,password:string){
    const {data} = await api.post<{access_token:string}>('/auth/login',{username,password})
    sessionStorage.setItem('lichu_token',data.access_token)
    try { await me() } catch(error){logout();throw error}
  }
  function logout(){sessionStorage.removeItem('lichu_token');user.value=null}
  return {user,me,login,logout}
})
