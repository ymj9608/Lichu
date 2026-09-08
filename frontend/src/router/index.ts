import {createRouter,createWebHistory} from 'vue-router'
import {useAuth} from '../stores/auth'
import AuthView from '../views/AuthView.vue'
import AppLayout from '../layouts/AppLayout.vue'
const router=createRouter({history:createWebHistory(),routes:[
  {path:'/login',component:AuthView,meta:{public:true}},
  {path:'/signup',component:AuthView,meta:{public:true}},
  {path:'/',component:AppLayout,children:[
    {path:'licenses',component:()=>import('../views/LicensesView.vue'),meta:{title:'라이선스 탐색',role:'USER'}},
    {path:'requests',component:()=>import('../views/RequestsView.vue'),meta:{title:'내 신청',role:'USER'}},
    {path:'my-licenses',component:()=>import('../views/MyLicensesView.vue'),meta:{title:'내 라이선스',role:'USER'}},
    {path:'admin',component:()=>import('../views/DashboardView.vue'),meta:{title:'대시보드',role:'MASTER'}},
    {path:'admin/requests',component:()=>import('../views/RequestsView.vue'),meta:{title:'신청 관리',role:'MASTER'}},
    {path:'admin/licenses',component:()=>import('../views/LicensesView.vue'),meta:{title:'라이선스 관리',role:'MASTER'}}]},
  {path:'/:pathMatch(.*)*',redirect:'/'}]})
router.beforeEach(async to=>{
  const auth=useAuth()
  if(!auth.user && sessionStorage.getItem('lichu_token')){try{await auth.me()}catch{auth.logout()}}
  if(to.meta.public)return auth.user ? (auth.user.role==='MASTER'?'/admin':'/licenses') : true
  if(!auth.user)return '/login'
  const home=auth.user.role==='MASTER'?'/admin':'/licenses'
  if(to.path==='/' || (to.meta.role && to.meta.role!==auth.user.role))return home
})
export default router
