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

  props :{
    state: null,
  },

  created() {
    fetchEnvelopeWorkflow(this.$route.params.envelope_id)
    .then((response) => {
      this.graphJson = response.data;
      this.data();
    })
    .catch((e) => {
      console.log(e);
    });
  },

  methods: {
    data(){
      let dataset = JSON.parse(JSON.stringify(this.graphJson));

      for (let node of dataset.graph.nodes) {
        node.color = 'grey';
        if (node.metadata.initial === true) {
          node.shape = 'doublecircle';
        }
         if(node.metadata.final === true) {
          node.shape = 'doublecircle';
        }
        if(this.state === node.id){
          node.style = 'filled';
          node.fontcolor = 'white';
          node.fillcolor = '#007bff';
        }
      }

      for (let edge of dataset.graph.edges) {
        edge.fillcolor = 'grey';
        edge.color = 'grey';
      }

      this.convertToDot(dataset)
    },

    convertToDot(data) {
      this.renderGraph(ToDot(data));
    },

    renderGraph(dot) {
      let new_dot = dot.split('\n');
      new_dot[0] = new_dot[0] + 'rankdir=LR;';
      let final_dot = new_dot.join('\n');
      this.graph = Viz(final_dot, { format: 'svg' });
    }
  },

  watch: {
    state: {
      handler(val, oldVal) {
        this.data();
      },
      deep: true,
    }
  },

};

</script>

<style lang="css">
.graph-container svg {
    width: 100%;
}
</style>
