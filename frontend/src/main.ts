import {createApp} from 'vue'
import {createPinia} from 'pinia'
import router from './router'
import App from './App.vue'
import {useAuth} from './stores/auth'
import './style.css'
const app=createApp(App)
app.use(createPinia()).use(router).mount('#app')
window.addEventListener('lichu:unauthorized',()=>{useAuth().logout();void router.replace('/login?expired=1')})
