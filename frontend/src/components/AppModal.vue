<script setup lang="ts">
import {onMounted,onUnmounted,ref} from 'vue'
import {X} from 'lucide-vue-next'
const props=defineProps<{title:string;wide?:boolean;busy?:boolean}>()
const emit=defineEmits<{close:[]}>()
const panel=ref<HTMLElement|null>(null)
let previous:HTMLElement|null=null
function keyboard(e:KeyboardEvent){
  if(e.key==='Escape' && !props.busy)emit('close')
  if(e.key==='Tab'){
    const nodes=panel.value?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select,textarea,a[href]')
    if(!nodes?.length)return
    const first=nodes[0],last=nodes[nodes.length-1]
    if(e.shiftKey && document.activeElement===first){e.preventDefault();last.focus()}
    else if(!e.shiftKey && document.activeElement===last){e.preventDefault();first.focus()}
  }
}
onMounted(()=>{previous=document.activeElement as HTMLElement;document.body.style.overflow='hidden';panel.value?.focus();document.addEventListener('keydown',keyboard)})
onUnmounted(()=>{document.body.style.overflow='';document.removeEventListener('keydown',keyboard);previous?.focus()})
</script>
<template><Teleport to="body"><div class="modal-backdrop" @mousedown.self="!busy && emit('close')"><section ref="panel" tabindex="-1" role="dialog" aria-modal="true" aria-labelledby="modal-title" class="modal" :class="{wide}"><header class="modal-header"><h2 id="modal-title">{{title}}</h2><button class="icon-button" aria-label="닫기" :disabled="busy" @click="emit('close')"><X :size="20"/></button></header><slot/></section></div></Teleport></template>
