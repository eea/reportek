<template>
  <div class="login-page">
  <b-form @submit="login">
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
                      placeholder="Enter password">
        </b-form-input>
      </b-form-group>
      <b-button type="submit" variant="primary">Log in</b-button>
    </b-form>
  </div>
</template>

<script>

import authMixin from '../mixins/auth';

export default {
  name: 'Login',

  mixins: [ authMixin ],

  data() {
    return {
      form: {
        username: '',
        password: '',
      },
    };
  },
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
