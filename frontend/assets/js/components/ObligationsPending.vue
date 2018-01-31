<template>
  <div class="hello">
    Obligations Pending
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
import { fetchObligationsPending } from '../api';

export default {
  name: 'EnvelopesWIP',

  data() {
    return {
      obligationsPending: [],
    };
  },

  created() {
    fetchObligationsPending()
      .then((response) => {
        // JSON responses are automatically parsed.
        this.obligationsPending = response.data.results;
      })
      .catch((e) => {
        console.log(e);
      });
  },
};
</script>

<style>

</style>
