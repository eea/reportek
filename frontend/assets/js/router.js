import Vue from 'vue';
import Router from 'vue-router';
import EnvelopeDetail from './components/EnvelopeDetail';
import EnvelopeCreate from './components/EnvelopeCreate';
import Dashboard from './components/Dashboard';
import EnvelopesArchive from './components/EnvelopesArchive';
import EnvelopesWIP from './components/EnvelopesWIP';
import ReportersList from './components/ReportersList';
import ObligationDetail from './components/ObligationDetail';
import ObligationsPending from './components/ObligationsPending';
import FileDetails from './components/FileDetails';
import Login from './components/Login';

Vue.use(Router);

const routes = [
  {
    path: '/',
    name: 'ReportersList',
    component: ReportersList,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/envelopes/archive',
    name: 'EnvelopesArchive',
    component: EnvelopesArchive,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/envelopes/wip',
    name: 'EnvelopesWIP',
    component: EnvelopesWIP,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/envelopes/:envelopeId(\\d+)',
    name: 'EnvelopeDetail',
    component: EnvelopeDetail,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/envelopes/:envelopeId(\\d+)/files/:fileId',
    name: 'FileDetails',
    component: FileDetails,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/envelopes/create',
    name: 'EnvelopeCreate',
    component: EnvelopeCreate,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/obligations/:obligationId',
    name: 'ObligationDetail',
    component: ObligationDetail,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/reporter/:reporterId/obligations',
    name: 'ObligationsPending',
    component: ObligationsPending,
    meta: { requiresAuth: true, adminAuth:false },
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '*',
    redirect: '/',
  },
];

const routerOptions = {
  routes,
  mode:'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
  base: '/',
}

const router = new Router(routerOptions);

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const authToken = window.$cookies.get('authToken');
    
    if (!authToken) {
      next({ name:'Login' });
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;
