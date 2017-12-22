<template>
  <div class="hello">
    <p> Envelope item</p>
    <div v-if="envelope">
      <p><strong>{{envelope.name}}</strong></p>
      <p>{{envelope.country}}</p>
      <p>{{envelope.created_at}}</p>
      <p>{{envelope.current_state}}</p>
      <p>{{envelope.created_at}}</p>
      <ul v-if="files && files.length">
        <li v-for="file of files" :key="file.id">
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
    }
  },

  // Fetches posts when the component is created.
  created() {
    fetchEnvelopeItem(this.$route.params.envelope_id)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelope = response.results;
      })
      .catch((e) => {
        console.log(e);
      });
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
