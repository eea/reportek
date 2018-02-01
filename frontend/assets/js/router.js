import Vue from 'vue';
import Router from 'vue-router';
import Envelopes from './components/Envelopes';
import EnvelopeDetail from './components/EnvelopeDetail';
import EnvelopeCreate from './components/EnvelopeCreate';
import Dashboard from './components/Dashboard';
import EnvelopesArchive from './components/EnvelopesArchive';
import EnvelopesWip from './components/EnvelopesWip';

Vue.use(Router);

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
  base: '/workspace',
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/envelopes/archive',
      name: 'EnvelopesArchive',
      component: EnvelopesArchive,
    },
    {
      path: '/envelopes/wip',
      name: 'EnvelopesWip',
      component: EnvelopesWip,
    },
    {
      path: '/envelopes/:envelope_id(\\d+)',
      name: 'EnvelopeDetail',
      component: EnvelopeDetail,
      meta: {
        breadcrumb: {
          name: 'Envelopes',
          path: '/envelopes/wip',
        },
      },
    },
    {
      path: '/envelopes/create',
      name: 'EnvelopeCreate',
      component: EnvelopeCreate,
    },
    {
      path: '*',
      redirect: '/',
    },
  ],
});
