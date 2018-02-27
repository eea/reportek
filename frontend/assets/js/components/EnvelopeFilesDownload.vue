<template>
  <div class="download-body">
    <b-list-group v-for="file in files">
        <b-list-group-item>
          <span style="flex-grow: 1" class="blue-color">
            {{file.name}}
          </span>
            <b-btn
              class="card-link"
              variant="primary"
              v-on:click.stop="getFileConversions(file)"
              v-show="file.availableConversions.length === 0"
            >
              Convert
            </b-btn>
            <b-form-select
              :options="file.availableConversions"
              v-model="file.selectedConversion"
              v-show="file.availableConversions.length > 1"
            >
            </b-form-select>
            <p v-show="file.availableConversions.length === 1">No conversions available</p>
          <b-btn
            variant="primary"
            v-on:click="convertScript(file)"
            v-show="file.availableConversions.length > 1"
          >

            Download converted
          </b-btn>
          <a download class="btn btn-white"  :href="file.file"> <i class="far fa-folder-open"></i> Download original </a>

        </b-list-group-item>


    </b-list-group>
    <b-button v-if="files.length > 1" class="download-all-button" variant="primary"> <i class="far fa-folder-open"></i>Download all</b-button>
  </div>
</template>


<script>
import {fetchEnvelopeFilesConvertScripts,
          runEnvelopeFilesConvertScript,
        } from '../api';

export default {
  name: 'EnvelopeFilesDownload',

  props: {
    files: {},
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
      if (file.selectedConversion) {
        runEnvelopeFilesConvertScript(this.$route.params.envelope_id, file.id, file.selectedConversion)
          .then((response) => {
            const fileName = response.headers['content-disposition'].split('filename=')[1];
            const fileType = response.headers['content-type'];
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
      a.download = filename;

      // Append anchor to body.
      document.body.appendChild(a);
      a.click();

      // Remove anchor from body
      document.body.removeChild(a);
    },
  },
};
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
    border: none;
    justify-content: space-between;
    align-items: center;
    &:last-of-type{
      border-bottom-right-radius: 0;
    }
  }
  select {
    max-width: 300px;
  }
  button, a {
    margin-left: 5px;
  }
}

.download-all-button {
    float: none;
    position: absolute;
    bottom: -50px;
    right: 6rem;
}

.modal-title {
  font-size: 2rem;
  margin-right: 1rem;
  margin-left: 1rem;
}
.modal-footer {
  border-top: none;
}

#downloadModal {
  .modal-footer > :not(:last-child) {
    display: none;
  }
}
</style>
