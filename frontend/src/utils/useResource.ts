import {ref,onMounted,onUnmounted} from 'vue'
import {errorOf} from '../api/client'
export function useResource(fetcher:()=>Promise<void>){
  const loading=ref(true), error=ref('')
  let running:Promise<void>|null=null, timer:ReturnType<typeof setInterval>, disposed=false
  async function refresh(quiet=false):Promise<void>{
    if(disposed)return
    // A mutation or filter change during polling must still trigger a fresh read.
    if(running){await running;return refresh(quiet)}
    if(!quiet)loading.value=true
    running=(async()=>{
      try{await fetcher();error.value=''}catch(e){error.value=errorOf(e).message}finally{loading.value=false}
    })()
    try{await running}finally{running=null}
  }
  const focus=()=>{if(document.visibilityState==='visible')void refresh(true)}
  onMounted(()=>{void refresh();window.addEventListener('focus',focus);timer=setInterval(focus,30000)})
  onUnmounted(()=>{disposed=true;clearInterval(timer);window.removeEventListener('focus',focus)})
  return {loading,error,refresh}
}
