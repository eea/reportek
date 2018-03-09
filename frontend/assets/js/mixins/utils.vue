<template>
</template>

<script>

import * as utils from '../utils/UtilityFunctions'
export default {

  name: 'utils',
  created(){
  },

  data () {
    return {

    }
  },

  methods: {
     envelopeCodeDictionary(status){
      const codeDictionary = {
        info: 'success',
        ok: 'success',
        error: 'danger',
        fail: 'danger',
        draft: 'Draft',
        auto_qa: 'Automatic QA',
        send_to_qa: 'Send to QA',
        reject: 'Reject',
        release: 'Release',
      };
      if (!status) {
        return '';
      }
      return codeDictionary[status.trim().toLowerCase()] || status;
    },

    envelopeCodeDictionaryVariants(status){
      const codeDictionary = {
        info: 'info',
        ok: 'primary',
        error: 'danger',
        fail: 'danger',
        draft: 'warning',
        auto_qa: 'secondary',
        send_to_qa: 'secondary',
        reject: 'danger',
        release: 'success',
      };
      if (!status) {
        return '';
      }
      return codeDictionary[status.trim().toLowerCase()] || status;
    },

    translateCode(code) {
      return this.envelopeCodeDictionary(code);
    },
    translateCodeVariant(code) {
      return this.envelopeCodeDictionaryVariants(code);
    },

    formatDate(date, format) {
      return utils.dateFormat(date,format);
    },

    formatSize(size, decimalPoint) {
      return utils.formatFileSize(size, decimalPoint);
    },

    capitalize(value) {
      return utils.capitalize(value);
    }

  },
}
</script>

<style lang="css" scoped>
</style>
