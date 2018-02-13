<template>
  <div>

    <div class="graph-container" v-html="graph"></div>
  </div>
</template>

<script>

import { fetchEnvelopeWorkflow } from '../api';
const Viz = require('viz.js');

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
      this.renderGraph(response.data.dot);
    })
    .catch((e) => {
      console.log(e);
    });
  },

  methods: {
    renderGraph(envelopeworkflow) {
      const workflowArray = envelopeworkflow.split('\n');
      workflowArray[2] = workflowArray[2] + 'rankdir=LR;';
      const finalgraph = workflowArray.join('\n');
      this.graph = Viz(finalgraph, { format: 'svg' });
    }
  },

};

</script>

<style lang="css">
.graph-container svg {
    width: 100%;
}
</style>
