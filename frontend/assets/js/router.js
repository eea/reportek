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

Vue.use(Router);

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
  base: '/workspace',
  routes: [
    {
      path: '/',
      name: 'ReportersList',
      component: ReportersList,
    },
    {
      path: '/reporter/:reporterId',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/reporter/:reporterId/envelopes/archive',
      name: 'EnvelopesArchive',
      component: EnvelopesArchive,
    },
    {
      path: '/reporter/:reporterId/envelopes/wip',
      name: 'EnvelopesWIP',
      component: EnvelopesWIP,
    },
    {
      path: '/reporter/:reporterId/envelopes/:envelopeId(\\d+)',
      name: 'EnvelopeDetail',
      component: EnvelopeDetail,
      // meta: {
      //   breadcrumb: {
      //     name: 'WIP Envelopes',
      //     path: '/envelopes/wip',
      //   },
      // },
    },
    {
      path: '/reporter/:reporterId/envelopes/create',
      name: 'EnvelopeCreate',
      component: EnvelopeCreate,
    },
    {
      path: '/reporter/:reporterId/obligations/:obligationId',
      name: 'ObligationDetail',
      component: ObligationDetail,
    },
    {
      path: '/reporter/:reporterId/obligations',
      name: 'ObligationsPending',
      component: ObligationsPending,
    },
    {
      path: '*',
      redirect: '/',
    },
  ],
});
