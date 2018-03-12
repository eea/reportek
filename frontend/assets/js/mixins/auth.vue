<template>
</template>

<script>
export default {

  methods: {
    login(evt) {
      evt.preventDefault();
      let date = new Date();

      date.setDate(date.getDate() + 0.01);
      this.$cookies.set('authToken', this.form.username, date);
      this.$router.push({ name: 'ReportersList' });
    },

    logout() {
      this.$cookies.remove('authToken');
      this.$router.push({ name: 'Login' });
    },
  },
}
</script>

<style>
</style>
