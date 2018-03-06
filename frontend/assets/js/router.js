import Vue from 'vue';
import Router from 'vue-router';
import Envelopes from './components/Envelopes';
import EnvelopeDetail from './components/EnvelopeDetail';
import EnvelopeCreate from './components/EnvelopeCreate';
import Dashboard from './components/Dashboard';
import EnvelopesArchive from './components/EnvelopesArchive';
import EnvelopesWIP from './components/EnvelopesWIP';
import ReportersList from './components/ReportersList';

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
      path: '/reporter/:id',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/reporter/:id/envelopes/archive',
      name: 'EnvelopesArchive',
      component: EnvelopesArchive,
    },
    {
      path: '/reporter/:id/envelopes/wip',
      name: 'EnvelopesWIP',
      component: EnvelopesWIP,
    },
    {
      path: '/reporter/:id/envelopes/:envelope_id(\\d+)',
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
      path: '/reporter/:id/envelopes/create',
      name: 'EnvelopeCreate',
      component: EnvelopeCreate,
    },
    {
      path: '*',
      redirect: '/',
    },
  ],
});
