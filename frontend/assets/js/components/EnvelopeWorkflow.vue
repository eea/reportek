<template>
  <div>
    <pre>{{graphJson}}</pre>
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
      graphJson: null
    };
  },

  created() {
    fetchEnvelopeWorkflow(this.$route.params.envelope_id)
    .then((response) => {
      // JSON responses are automatically parsed.
      this.graphJson = response.data;
      console.log(response.data)
      this.data()
    })
    .catch((e) => {
      console.log(e);
    });
  },

  methods: {
    data(){
      let dataset = this.graphJson

      console.log(dataset)

      this.convertToDot(dataset)
    },

    convertToDot(data) {
      this.renderGraph(toDot(data))
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
