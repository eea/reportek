<template>
  <div class="download-body">
    <b-list-group v-for="file in files">
        <b-list-group-item>
          <span class="blue-color">
            {{file.name}}
          </span>
            <b-link
             href="#"
              class="card-link"
              v-on:click.stop="getFileConversions(file)"
              v-show="file.availableConversions.length === 0"
            >
              <p>Choose Conversion</p>
            </b-link>
            <b-form-select
              :options="file.availableConversions"
              v-model="file.selectedConversion"
              v-show="file.availableConversions.length > 1"
            >
            </b-form-select>
            <p v-show="file.availableConversions.length === 1">No conversions available</p>
               <b-link
            href="#"
            class="card-link"
            v-on:click="convertScript(file)"
            v-show="file.availableConversions.length > 1"
          >

            <p>Download </p>
          </b-link>
          <a download class="btn btn-white"  v-show="file.availableConversions.length <= 1" :href="file.file"> <i class="far fa-folder-open"></i> Download original </a>
          <b-btn
            class="btn btn-white"
            v-on:click="convertScript(file)"
            v-show="file.availableConversions.length > 1"
          >
          Download converted
          </b-btn>
        </b-list-group-item>


    </b-list-group>
    <b-button variant="white"> <i class="far fa-folder-open"></i>Download all</b-button>
    <div slot="modal-header">sfafas</div>
  </div>
</template>


<script>
import {fetchEnvelopeFilesConvertScripts,
          runEnvelopeFilesConvertScript
        } from '../api';

export default {

  name: 'EnvelopeFilesDownload',

  props: {
    files: {}
  },

  data () {
    return {

    }
  },

  methods: {
    getFileConversions(file) {
      fetchEnvelopeFilesConvertScripts(this.$route.params.envelope_id, file.id)
        .then((response) => {
          file.availableConversions.push({value: null, text: 'Please select conversion'});
          response.data.map((script) => {
            file.availableConversions.push({value: script.convert_id, text: script.result_type});
            return script;
          });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    convertScript(file) {
      if(file.selectedConversion) {
        runEnvelopeFilesConvertScript(this.$route.params.envelope_id, file.id, file.selectedConversion)
          .then((response) => {
            // console.log('Converted file: ', response.data);
            const fileName = response.headers["content-disposition"].split('filename=')[1];
            const fileType = response.headers["content-type"];
            console.log(response)
            this.download(response.data, fileName, fileType);
          })
          .catch((error) => {
            console.log(error);
          });
      }
    },

    download(blob, filename, filetype) {
        let a = window.document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([blob], {type: filetype}));
        console.log(a.href)
        a.download = filename;

        // Append anchor to body.
        document.body.appendChild(a);
        a.click();

        // Remove anchor from body
        document.body.removeChild(a);
      },
  },
}
</script>

<style lang="scss">
@media (min-width: 992px){
  .modal-lg {
      max-width: 1200px!important;
  }
}

.download-body {
  .list-group-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
