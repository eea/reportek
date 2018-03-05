<template>
  <div>
    <pre v-if="obligation">
      {{obligation}}
    </pre>
  </div>
</template>

<script>

import { fetchObligation } from '../api';

export default {

  name: 'ObligationDetail',

  data(){
    return {
      obligation: null
    }
  },

  created() {
    fetchObligation(this.$route.params.obligationId)
      .then((response) => {
        this.obligation = response.data
        console.log(response.data)
      })
      .catch((error) => {
        console.log(error)
      })
  },
}
</script>

<style lang="css" scoped>
</style>
