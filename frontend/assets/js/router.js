import Vue from 'vue';
import Router from 'vue-router';
import Envelopes from './components/Envelopes';
import EnvelopeItem from './components/EnvelopeItem';

Vue.use(Router);

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => ({ y: 0 }),
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
      path: '/envelopes/:envelope_id',
      name: 'EnvelopeItem',
      component: EnvelopeItem,
    },
    {
      path: '*',
      redirect: '/',
    },
  ],
});
