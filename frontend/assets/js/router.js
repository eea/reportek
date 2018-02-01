import Vue from 'vue';
import Router from 'vue-router';
import Envelopes from './components/Envelopes';
import EnvelopeDetail from './components/EnvelopeDetail';

Vue.use(Router);

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
  base: '/workspace',
  routes: [
    {
      path: '/',
      component: Envelopes,
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
      path: '*',
      redirect: '/',
    },
  ],
});
