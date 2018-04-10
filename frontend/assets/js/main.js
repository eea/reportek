// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import App from './App';
import router from './router';
import '../css/main.scss';
import VueCookies from 'vue-cookies'
import ChannelsPlugin from './setup/ChannelsPlugin';
import { i18n } from './setup/i18n-setup';

const channelOptions = { debug: true, reconnectInterval: 3000 };

Vue.use(BootstrapVue);
Vue.use(ChannelsPlugin, channelOptions);
Vue.use(VueCookies);

Vue.config.productionTip = false;

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: { App },
  i18n
});
