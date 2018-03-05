<template>
</template>

<script>
export default {

  name: 'utils',
  created(){
    console.log('asdasfasf')
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
        auto_qa: 'default',
        send_to_qa: 'default',
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

  },
}
</script>

<style lang="css" scoped>
</style>
