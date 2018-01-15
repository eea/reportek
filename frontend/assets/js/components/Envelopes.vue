<template>
  <div class="hello">
    <ul v-if="envelopes && envelopes.length">
      <li
        v-for="envelope of envelopes"
        :key="envelope.id">
        <a v-bind:href="`/envelopes/${envelope.id}`">
          <p><strong>{{envelope.name}}</strong></p>
        </a>
        <p>country id - {{envelope.country}}</p>
      </li>
    </ul>

    <p v-if="!envelopes || envelopes.length == 0"> No envelopes created yet</p>
  </div>
</template>

<script>
import { fetchEnvelopes } from '../api';

export default {
  name: 'Envelopes',

  data() {
    return {
      envelopes: [],
    };
  },

  created() {
    fetchEnvelopes()
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelopes = response.data.results;
      })
      .catch((e) => {
        // console.log(e);
      });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
