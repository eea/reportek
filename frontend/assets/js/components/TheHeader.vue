<template>
  <div>
  <b-navbar
    toggleable="md"
    type="dark"
    variant="info"
  >
    <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
    <b-navbar-brand href="/">Home</b-navbar-brand>
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

        <b-nav-item-dropdown right>
          <!-- Using button-content slot -->
          <template slot="button-content">
            <em>User</em>
          </template>
          <b-dropdown-item href="#">Profile</b-dropdown-item>
          <b-dropdown-item href="#">Signout</b-dropdown-item>
        </b-nav-item-dropdown>

      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
  </div>
</template>

<script>
export default {
  name: 'TheHeader',
  data() {
    return {
      breadcrumbs: [],
    };
  },
  watch: {
    $route(to, from) {
      this.breadcrumbs = this.makeBreadcrumbs();
    },
  },
  created() {
    this.breadcrumbs = this.makeBreadcrumbs();
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
  },
};
</script>

<style>
</style>
