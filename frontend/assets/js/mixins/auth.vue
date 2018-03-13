<template>
</template>

<script>
import { getLoginToken, removeLoginToken } from '../api';

export default {

  methods: {
    login(evt) {
      evt.preventDefault();

      getLoginToken(this.form.username, this.form.password)
      .then((response) => {
        console.log(response.data)
          let date = new Date();

      date.setDate(date.getDate() + 30);
      this.$cookies.set('authToken', response.data.token, date);
      this.$router.push({ name: 'ReportersList' });
      })
    },

    logout() {
        // var p = new Promise((resolve, reject) => {
          removeLoginToken().then((response)=> {
          this.$cookies.remove('authToken');
          this.$router.push({ name: 'Login' });
          })
          // resolve()
        // })

        // p.then(()=>{
        //   console.log(this.$cookies.get('authToken'));
        // })
    },
  },
}
</script>

<style>
</style>
