<template>
  <div>

    <div class="graph-container" v-html="graph"></div>
  </div>
</template>

<script>

import { fetchEnvelopeWorkflow } from '../api';
const Viz = require('viz.js');
const toDot = require("jgf-dot");

export default {

  name: 'EnvelopeWorkflow',

  data() {
    return {
      graph: '',
    };
  },

  created() {

    fetchEnvelopeWorkflow(this.$route.params.envelope_id)
    .then((response) => {
      // JSON responses are automatically parsed.
      this.convertToDot(response.data);
    })
    .catch((e) => {
      console.log(e);
    });
  },

  methods: {
    convertToDot(graphJson) {
      return this.renderGraph(toDot(graphJson))
    },
    renderGraph(dot) {
      this.graph = Viz(dot, { format: 'svg' });
    }
  },

};

</script>

<style lang="css">
.graph-container svg {
    width: 100%;
}
</style>
