<template>
  <div class="hello">
    Envelope Archive
    <div v-if="envelopes && envelopes.length">
      <b-table
        :hover="false"
        :items="envelopes"
        :fields="fields"
      >
        <router-link
          slot="name"
          slot-scope="envelope"
          class="nav-link"
          :to="`/envelopes/${envelope.item.id}`"
        >
          {{envelope.value}}
        </router-link>
      </b-table>
    </div>

    <p v-if="!envelopes || envelopes.length == 0"> No envelopes finalized yet</p>
  </div>
</template>

<script>
import { fetchArchiveEnvelopes } from '../api';

export default {
  name: 'EnvelopesArchive',

  data() {
    return {
      fields: ['name', 'files_count', 'created_at', 'finalized', 'reporting_period_start', 'reporting_period_end'],
      envelopes: [],
    };
  },

  created() {
    fetchArchiveEnvelopes(this.$route.params.id)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelopes = response.data;
      })
      .catch((e) => {
        console.log(e);
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
