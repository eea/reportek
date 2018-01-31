<template>
  <div class="hello">
    WIP
    <b-container class="bv-example-row">
        <b-row>
            <b-col cols="2">Ramsar</b-col>
            <b-col cols="10">
              <b-row>7.1 Trees</b-row>
              <b-row>7.2 Animals</b-row>
            </b-col>
        </b-row>
        <b-row>
          <b-col cols="2">Ramsar</b-col>
          <b-col cols="10">
            <b-row>7.1 Trees</b-row>
            <b-row>7.2 Animals</b-row>
          </b-col>
        </b-row>
    </b-container>
  </div>
</template>

<script>
import { fetchWipEnvelopes } from '../api';

export default {
  name: 'EnvelopesWIP',

  data() {
    return {
      envelopesWIP: [],
    };
  },

  created() {
    fetchWipEnvelopes()
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelopesWIP = response.data.results;
      })
      .catch((e) => {
        console.log(e);
      });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
