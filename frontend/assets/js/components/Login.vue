<template>
  <div class="login-page">
  <b-form @submit="onSubmit" @reset="onReset">
      <b-form-group id="exampleInputGroup2"
                    label="Username"
                    label-for="username">
        <b-form-input id="username"
                      type="text"
                      v-model="form.username"
                      required
                      placeholder="Enter username">
        </b-form-input>
      </b-form-group>
      <b-form-group id="exampleInputGroup1"
                    label="Password"
                    label-for="password"
      >
        <b-form-input id="password"
                      type="password"
                      v-model="form.password"
                      required
                      placeholder="Enter email">
        </b-form-input>
      </b-form-group>
      <b-button type="submit" variant="primary">Log in</b-button>
    </b-form>
  </div>
</template>

<script>
export default {

  name: 'Login',

  data() {
    return {
      form: {
        username: '',
        password: '',
      },
    }
  },

  methods: {
    onSubmit(evt) {
      evt.preventDefault();
      console.log(JSON.stringify(this.form));

      let date = new Date;
      date.setDate(date.getDate() + 0.001);
      this.$cookies.set('authToken', this.form.username, date)
      this.$router.push({ name: 'ReportersList' });

    },
    onReset(evt) {
      evt.preventDefault();
    }
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  justify-content:center;
  height: calc(100vh - 64px);
  align-items: center;
  form {
    max-width: 350px;
    width: 100%;
  }

  .btn {
    min-width: 200px;
  }
}
</style>
