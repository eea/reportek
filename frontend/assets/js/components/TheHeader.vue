<template>
  <b-navbar
    toggleable="md"
    type="light"
    sticky
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

        <b-nav-item-dropdown right v-if="currentCountry">
          <!-- Using button-content slot -->
          <template slot="button-content">
            <em>Reporting for
              <span v-bind:class="[countryStyleClass, 'flag-icon']">{{currentCountry.name}}</span>
            </em>
          </template>
          <b-dropdown-item 
            v-for="country in userProfile.reporters"
            :key="country.id"
            :to="{ name: 'Dashboard', params: { reporterId: country.id }}"
          >
                      <!-- :to="{ name: 'Dashboard', params: { reporterId: country.id }}" -->

            <span v-bind:class="[countryFlag(country.abbr), 'flag-icon']">{{country.name}}</span>
          </b-dropdown-item>
        </b-nav-item-dropdown>

        <b-nav-item-dropdown right v-if="userProfile">
          <!-- Using button-content slot -->
          <template slot="button-content">
            <em>{{userProfile.username}}</em>
          </template>
          <b-dropdown-item href="#">Profile</b-dropdown-item>
          <b-dropdown-item href="#">Signout</b-dropdown-item>
        </b-nav-item-dropdown>

      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</template>

<script>
import { fetchUserProfile } from '../api';

export default {
  name: 'TheHeader',

  data() {
    return {
      breadcrumbs: [],
      currentCountry: null,
      userProfile: null,
      countryStyleClass: null,
    };
  },

  created() {
    this.breadcrumbs = this.makeBreadcrumbs();
    this.getUserProfile();
    this.handeCountryChange(this.$route.params.reporterId);
  },

  watch: {
    $route(to, from) {
      this.breadcrumbs = this.makeBreadcrumbs();
      this.handeCountryChange(to.params.reporterId);
    },
  },

  methods: {
    makeBreadcrumbs() {
      const crumbs = [];
      for (let i = 0; i < this.$route.matched.length; i += 1) {
        if (this.$route.matched[i].meta && this.$route.matched[i].meta.breadcrumb) {
          const paramIdName = Object.keys(this.$route.params)[0];
          const paramIdValue = this.$route.params[paramIdName];
          const path = this.$route.matched[i].meta.breadcrumb.path.replace(paramIdName, paramIdValue).replace(':', '');
          const name = this.$route.matched[i].meta.breadcrumb.name;
          crumbs.push({ path, name });
        }
      }
      return crumbs;
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
      if(!newCountry) {
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
        let currentCountryIndex = this.userProfile.reporters.findIndex(country => String(country.id) == newCountry);
        
        this.currentCountry = this.userProfile.reporters[currentCountryIndex];
        this.countryStyleClass = 'flag-icon-' + this.currentCountry.abbr.toLowerCase();
    },

    countryFlag(countryAbbr) {
      return 'flag-icon-' + countryAbbr.toLowerCase();
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
</style>
