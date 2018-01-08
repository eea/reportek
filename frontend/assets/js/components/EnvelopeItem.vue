<template>
  <div class="hello">
    <p> Envelope item</p>
    <div v-if="envelope">
      <p><strong>name: {{envelope.name}}</strong></p>
      <p>country: {{envelope.country}}</p>
      <p>reporting_period: {{envelope.reporting_period.start}}</p>
      <p>reporting_period: {{envelope.created_at.end}}</p>
      <p>current_state {{envelope.current_state}}</p>
      <p>created_at {{envelope.created_at}}</p>
      <p>Files: </p>
      <ul v-if="envelope.files && envelope.files.length">
        <li v-for="file of envelope.files" :key="file.id">
          <a v-bind:href="file.url">{{file.name}}</a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { fetchEnvelopeItem } from '../api';

export default {
  name: 'EnvelopeItem',
  data() {
    return {
      envelope: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    fetchEnvelopeItem(this.$route.params.envelope_id)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelope = response.data;
      });
      // .catch((e) => {
      //   // consol-e.log(e);
      // });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
