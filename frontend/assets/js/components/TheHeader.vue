<template>
  <b-navbar
    toggleable="md"
    type="light"
    sticky
    v-if="!doNotRender"
    variant="white"
  >
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand class="brand-link" to="/">Reportek</b-navbar-brand>
    <b-collapse is-nav id="nav_collapse">

      <b-navbar-nav>
        <router-link
          class="nav-link"
          :to="crumb.path"
          v-for="crumb in breadcrumbs"
          :key='crumb.name'
        >{{crumb.name}}
        </router-link>
      </b-navbar-nav>

      <!-- Right aligned nav items -->
      <b-navbar-nav class="ml-auto">

        <!-- country select -->
        <b-nav-item-dropdown right v-if="currentCountry">
          <!-- Using button-content slot -->
          <template slot="button-content">
            <em>{{ $t('reporting_for') }}
              <span v-bind:class="[countryStyleClass, 'flag-icon']"></span>{{currentCountry.name}}
            </em>
          </template>
          <b-dropdown-item
            v-for="country in userProfile.reporters"
            :key="country.id"
            :to="{ name: 'Dashboard', params: { reporterId: country.id }}"
          >
            <span v-bind:class="[countryFlag(country.abbr), 'flag-icon']"></span>{{country.name}}
          </b-dropdown-item>
        </b-nav-item-dropdown>

        <!-- language select -->
        <em>
          Language
          <span>{{currentLang}}</span>
        </em>
        <b-nav-item-dropdown right>
          <!-- Using button-content slot -->
          <b-dropdown-item
            v-for="lang in availableLanguages"
            :key='lang.lang'
            @click="setLang(lang)"
            href="#"
          >
           {{lang.text}}
          </b-dropdown-item>
        </b-nav-item-dropdown>

        <!-- user select -->
        <b-nav-item-dropdown right v-if="userProfile">
          <!-- Using button-content slot -->
          <template slot="button-content">
            <em>{{userProfile.username}}</em>
          </template>
          <b-dropdown-item href="#">Profile</b-dropdown-item>
          <b-dropdown-item @click="logout" href="#">Log out</b-dropdown-item>
        </b-nav-item-dropdown>


      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</template>

<script>
import { fetchUserProfile, setApiLang, getSupportedLanguages } from '../api';
import authMixin from '../mixins/auth'

export default {
  name: 'TheHeader',

  mixins: [authMixin],

  data() {
    return {
      doNotRender: false,
      breadcrumbs: [],
      currentCountry: null,
      userProfile: null,
      countryStyleClass: null,
      currentLang: null,
      availableLanguages: [],
    };
  },


  created() {
    this.renderFunction();
    this.getAvailableLanguages();
  },

  watch: {
    $route(to, from) {
      this.handeCountryChange(to.params.reporterId);
    },
  },

  methods: {
    setLang(lang) {
      this.currentLang = lang.text;
      this.$router.push({ query: { lang: lang.lang }});
    },

    getAvailableLanguages() {
      getSupportedLanguages()
        .then((langs) => { 
          this.availableLanguages = langs;
          const langObj = this.availableLanguages[this.$i18n.locale] || this.availableLanguages[this.$i18n.fallbackLocale];
          this.currentLang = langObj.text;
        });
    },

    renderFunction() {
      if(this.$cookies.get('authToken')) {
        this.doNotRender = false;
        this.getUserProfile();
        this.handeCountryChange(this.$route.params.reporterId);
      }
      else {
        this.doNotRender = true;
      }
    },

    getUserProfile() {
      return new Promise((resolve, reject) => {
        fetchUserProfile()
          .then((response) => {
            this.userProfile = response.data;
            resolve();
          })
          .catch((e) => {
            console.log(e);
            reject(error);
          });
      });
    },

    handeCountryChange(newCountry) {
      if (!newCountry) {
        this.currentCountry = null;
        this.countryStyleClass = null;
        return;
      }

      if (this.userProfile) {
        this.renderUserInfo(newCountry);
      } else {
        this.getUserProfile()
          .then((response) => {
            this.renderUserInfo(newCountry);
          })
          .catch((e) => {
            console.log(e);
          });
      }
    },

    renderUserInfo(newCountry) {
      const currentCountryIndex = this.userProfile.reporters.findIndex(country => String(country.id) == newCountry);

      this.currentCountry = this.userProfile.reporters[currentCountryIndex];
      this.countryStyleClass = 'flag-icon-' + this.currentCountry.abbr.toLowerCase();
    },

    countryFlag(countryAbbr) {
      return 'flag-icon-' + countryAbbr.toLowerCase();
    },
  },
  watch: {
    $route(to, from) {
      this.renderFunction();
    },
  },
};
</script>

<style>
.brand-link {
  font-size: 30px;
  font-weight: bold;
  line-height: 1.2;
  color: #17beb4!important;
}
.navbar {
  border-bottom: 2px solid #EEE;
}

.navbar-collapse .flag-icon {
  margin-right: .5rem;
}
</style>
