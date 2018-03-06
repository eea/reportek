<template>
  <div v-if="file">
    <h1>{{file.name}}</h1>
    <pre>
      {{file}}
    </pre>
  </div>
</template>

<script>

import {  fetchEnvelope,
          fetchEnvelopeFile,
          updateFile,
          removeFile,
        } from '../api';

import { dateFormat } from '../utils/UtilityFunctions';
import utilsMixin from '../mixins/utils';

export default {

  name: 'FileDetails',
  created(){
    fetchEnvelopeFile(this.$route.params.envelopeId, this.$route.params.fileId)
      .then((response) => {
        this.file = response.data
        console.log(response.data)
      })
  },

  data () {
    return {
      file: null,
    }
  }
}
</script>

<style lang="scss" scoped>
</style>
