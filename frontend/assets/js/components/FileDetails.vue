<template>
  <div class="file-page" v-if="file">
    <h1>{{envelopeName}}</h1>
    <b-row>
      <b-col class="file-details-wrapper" lg="6">
        <div class="file-details">
          <div class="file-details-header">
          <label>File name</label>
            <h4 v-if="!isEditing">{{file.name}}</h4>
            <b-form-input
                type="text"
                v-model="file.name"
                style="margin: 0 1rem;"
                v-else
              >
            </b-form-input>
          </div>
          <div class="file-details-section">
            <label>File size</label>
            <div>{{file.size}} kb</div>
          </div>
          <div class="file-details-section">
            <label>Last modified</label>
            <div>{{file.updated}}</div>
          </div>
          <div class="file-type">
            .XML
          </div>
        </div>
        <div class="file-actions">
          <div class="actions-section">
            <div v-if="!file.restricted" style="color:#1ea83a;"><i class="fas fa-eye"></i> Public file</div>
            <div v-else style="color: red;"><i class="fas fa-eye"></i> Restricted file</div>

            <b-btn v-if="!file.restricted" @click="restricFile(!file.restricted)" variant="link">Restrict from public</b-btn>
            <b-btn v-else @click="restricFile(!file.restricted)" variant="link">Make file public</b-btn>

          </div>
          <div class="actions-section">
             <b-link @click="showModal"
               href="#">Download</b-link>
          </div>
           <div class="actions-section">
            <b-btn
             variant="link"
             @click="renameFile()"
             v-if="!isEditing"
            >
              Rename
            </b-btn>
            <b-btn
              variant="link"
              @click="updateFile()"
              v-if="isEditing"
            >
              Save File
            </b-btn>

            <b-btn
              style="color: red"
              @click="deleteFile"
              variant="link"
            >
              Remove
            </b-btn>
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
     <b-modal v-if="modalFile" id="downloadModal" ref="downloadModal" size="lg" title="Download">
          <filesdownload :files="modalFile"></filesdownload>
    </b-modal>
  </div>
</template>

<script>
import {  fetchEnvelope,
          fetchEnvelopeFile,
          updateFile,
          updateFileRestriction,
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
      modalFile: [],
      envelopeName: null,
      fileQaScripts: null,
      isEditing: false,
    }
  },

  components: {
    filesdownload: EnvelopeFilesDownload,
  },

  created(){
   this.getFile()
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

    restricFile(restriction){
      updateFileRestriction(this.$route.params.envelopeId, this.file.id, restriction)
        .then((response) => {
          this.getFile()
        })
    },

    createModalFile(){
       this.modalFile[0] = Object.assign(
          {},
          this.modalFile[0],
          {
            availableConversions: [],
            selectedConversion: null,
          });
    },

    deleteFile() {
      removeFile(this.$route.params.envelopeId, this.$route.params.fileId)
        .then((response) => {
          this.$router.push({ name: 'EnvelopeDetail', params: { reporterId: this.$route.params.reporterId, envelopeId: this.$route.params.envelopeId } });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    showModal() {
      this.createModalFile();
      this.$refs.downloadModal.show();
    },

    runAllQaScripts(){
      for(let script of this.fileQaScripts) {
        this.runQAScript(this.file, script.id)
      }
    },

    getFile(){
      fetchEnvelopeFile(this.$route.params.envelopeId, this.$route.params.fileId)
        .then((response) => {
          this.file = response.data
          console.log(response.data)
          this.modalFile.push(response.data)
          this.createModalFile()
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


    renameFile() {
      this.isEditing = true;
    },

    updateFile() {
      updateFile(this.$route.params.envelopeId, this.file.id, this.file.name)
        .then((response) => {
          this.getFile()
        })
        .catch((error) => {
          console.log(error);
        });
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
