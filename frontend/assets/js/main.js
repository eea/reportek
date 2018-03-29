// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import BootstrapVue from 'bootstrap-vue';
import Vue from 'vue';
import App from './App';
import router from './router';
import '../css/main.scss';
import VueCookies from 'vue-cookies'
import ChannelsPlugin from './mixins/ChannelsPlugin';

const channelOptions = { debug: true, reconnectInterval: 3000 }
// Globally register bootstrap-vue components
Vue.use(BootstrapVue);
Vue.use(ChannelsPlugin, channelOptions);
// Globally register vue cookies
Vue.use(VueCookies)
Vue.config.productionTip = false;

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  template: '<App/>',
  components: { App },
});
