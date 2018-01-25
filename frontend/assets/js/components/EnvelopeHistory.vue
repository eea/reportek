<template>
      <b-card title="History">
        <p>envelopeHistory</p>
      </b-card>
</template>

<script>
import { fetchEnvelopeHistory } from '../api';
export default {
  name: 'EnvelopeItem',
  components: {
    'history': History,
  },
  data() {
    return {
      envelopeHistory: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.getEnvelopeHistory();
  },

  methods: {
    getEnvelopeHistory() {
      fetchEnvelopeHistory(this.$route.params.envelope_id)
        .then((response) => {
          this.envelopeHistory = response.data;
        });
    },
  },
}
</script>

<style lang="scss" scoped>

</style>
