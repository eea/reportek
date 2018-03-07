<template>
  <div class="file-page" v-if="file">
    <h1>{{envelopeName}}</h1>
    <b-row>
      <b-col class="file-details-wrapper" lg="6">
        <div class="file-details">
          <div class="file-details-header">
          <label>File name</label>
            <h4>{{file.name}}</h4>
          </div>
          <div class="file-details-section">
            <label>File size</label>
            <div>699kb</div>
          </div>
          <div class="file-details-section">
            <label>Last modified</label>
            <div>Ieri</div>
          </div>
          <div class="file-type">
            .XML
          </div>
        </div>
        <div class="file-actions">
          <div class="actions-section">
            <div style="color:#1ea83a;"><i class="fas fa-eye"></i> Public file</div>
            <b-btn variant="link">Restrict from public</b-btn>
          </div>
          <div class="actions-section">
             <b-link href="#">Download</b-link>
          </div>
           <div class="actions-section">
            <b-btn variant="link">Rename</b-btn>
            <b-btn style="color: red" variant="link">Remove</b-btn>
          </div>
        </div>
      </b-col>
      <b-col class="file-qa-wrapper" lg="6">
        <div v-if="fileQaScripts" class="file-qa">

          <h3>Quality assesment</h3>
          <div>{{fileQaScripts.length}} tests<b-btn @click="runAllQaScripts" variant="link"> Run all tests</b-btn></div>
          <div  class="qa-tests">
            <div
              v-for="script in fileQaScripts"
              :key="script.id">
              Test:
              <b-btn
                variant="link"
                v-on:click.stop="runQAScript(file, script.id)"
                >
                {{script.title}}
              </b-btn>
            </div>
          </div>

        </div>
      </b-col>
    </b-row>
  </div>
</template>

<script>
import {  fetchEnvelope,
          fetchEnvelopeFile,
          updateFile,
          removeFile,
          fetchEnvelopeFilesQAScripts,
          runEnvelopeFilesQAScript,
        } from '../api';

import { dateFormat } from '../utils/UtilityFunctions';
import utilsMixin from '../mixins/utils';
import EnvelopeFilesDownload from './EnvelopeFilesDownload';


export default {

  name: 'FileDetails',

  data() {
    return {
      file: null,
      envelopeName: null,
      fileQaScripts: null,
    }
  },

  created(){
    fetchEnvelopeFile(this.$route.params.envelopeId, this.$route.params.fileId)
      .then((response) => {
        this.file = response.data
        fetchEnvelopeFilesQAScripts(this.$route.params.envelopeId, this.$route.params.fileId)
        .then((response) => {
          let scripts = response.data
          for(let script of scripts) {
            script.status = null
          }

          this.fileQaScripts = scripts

        })
      }).catch((error) => {
        console.log(error)
      })
    fetchEnvelope(this.$route.params.envelopeId).then((response) => {
      this.envelopeName = response.data.name
    }).catch((error) => {
      console.log(error)
    })
  },

  methods: {
    runQAScript(file, scriptId) {
      runEnvelopeFilesQAScript(this.$route.params.envelopeId, file.id, scriptId)
        .then((response) => {
          file.availableScripts.map((script) => {
            if (script.data.id === scriptId) {
              script.variant = this.envelopeCodeDictionary(response.data.feedback_status);
            }
            return script;
          });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    runAllQaScripts(){
      for(let script of this.fileQaScripts) {
        this.runQAScript(this.file, script.id)
      }
    },

  }

}
</script>

<style lang="scss" scoped>
.file-details {
  background: url('../../img/file-background.svg');
  background-repeat: no-repeat;
  background-size: cover;
  min-height: 386px;
  padding: 1rem;
  max-width: 320px;;
  position: relative;

  .file-details-header {
    width: 89%;
    word-break: break-word;
    margin-top: 1rem;
    margin-bottom: 2rem;
  }

  .file-type {
    background: #fe7171;
    font-size: 1.6rem;
    display: inline-block;
    padding: .5rem 1.5rem;
    color: white;
    font-weight: bold;
    position: absolute;
    top: 40%;
    right: -12px;
    transform: translateY(-40%);
  }


  .file-details-section {
    border-top: 2px solid #ddd;
    width: 60%;
    margin-bottom: 2rem;
  }

  label {
    font-size: .8rem;
    color: #757575;
  }
}

.file-actions {
  a {
    padding: 0.375rem 0.75rem;
  }
  .btn-link {
    font-size: 16px!important;
    display: block;
  }

  .actions-section {
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #ddd;
    &:last-of-type {
      border-bottom: none;
    }
  }

}

.file-qa-wrapper {
  border-left: 1px solid #ddd;
}

.file-details-wrapper {
  display: flex;
  justify-content: space-between;
}
.file-page {
  h1 {
    margin: 2rem 0;
  }
}
</style>
