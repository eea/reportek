<template>
  <div>
    <div class="graph-container" v-html="graph"></div>
  </div>
</template>

<script>

import { fetchEnvelopeWorkflow } from '../api';

const Viz = require('viz.js');
const ToDot = require('jgf-dot');

export default {
  name: 'EnvelopeWorkflow',

  data() {
    return {
      graph: '',
      graphJson: null,
    };
  },

  props: {
    state: null,
  },

  created() {
    fetchEnvelopeWorkflow(this.$route.params.envelopeId)
    .then((response) => {
      this.graphJson = response.data;
      this.data();
    })
    .catch((e) => {
      console.log(e);
    });
  },

  methods: {
    data() {
      const dataset = JSON.parse(JSON.stringify(this.graphJson));

      for (let node of dataset.graph.nodes) {
        node.color = 'grey';
        if (node.metadata.initial === true) {
          node.shape = 'doublecircle';
        }
        if (node.metadata.final === true) {
          node.shape = 'doublecircle';
        }
        if (this.state === node.id) {
          node.style = 'filled';
          node.fontcolor = 'white';
          node.fillcolor = '#007bff';
        }
      }

      for (let edge of dataset.graph.edges) {
        edge.fillcolor = 'grey';
        edge.color = 'grey';
      }

      this.convertToDot(dataset);
    },

    convertToDot(data) {
      this.renderGraph(ToDot(data));
    },

    renderGraph(dot) {
      let newDot = dot.split('\n');
      newDot[0] = newDot[0] + 'rankdir=LR;';
      const finalDot = newDot.join('\n');
      this.graph = Viz(finalDot, { format: 'svg' });
    },
  },

  watch: {
    state: {
      handler(val, oldVal) {
        this.data();
      },
      deep: true,
    },
  },

};

</script>

<style lang="css">
.graph-container svg {
    width: 100%;
}
</style>
