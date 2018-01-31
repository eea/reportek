import Vue from 'vue';
import Router from 'vue-router';
import Envelopes from './components/Envelopes';
import EnvelopeDetail from './components/EnvelopeDetail';
import EnvelopeCreate from './components/EnvelopeCreate';
import Dashboard from './components/Dashboard';
import EnvelopesArchive from './components/EnvelopesArchive';

Vue.use(Router);

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/archive',
      name: 'EnvelopesArchive',
      component: EnvelopesArchive,
    },
    {
      path: '/envelopes',
      name: 'Envelopes',
      component: Envelopes,
    },
    {
      path: '/envelopes/:envelope_id(\\d+)',
      name: 'EnvelopeDetail',
      component: EnvelopeDetail,
      meta: {
        breadcrumb: {
          name: 'Envelopes',
          path: '/envelopes',
        },
      },
    },
    {
      path: '/envelopes/create',
      name: 'EnvelopeCreate',
      component: EnvelopeCreate,
      meta: {
        breadcrumb: {
          name: 'Envelopes',
          path: '/envelopes',
        },
      },
    },
    {
      path: '*',
      redirect: '/',
    },
  ],
});
