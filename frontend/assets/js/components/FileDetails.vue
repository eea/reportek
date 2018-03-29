<template>
  <div class="file-page" v-if="file">
   <div class="breadcrumbs">
      <router-link
         :to="{name:'Dashboard', params: {reporterId: `${$route.params.reporterId}`}}"
        >
        Dashboard
      </router-link>

      <span class="separator">/</span>
      <router-link
         :to="{name:'EnvelopesWIP', params: {reporterId: `${$route.params.reporterId}`}}"
         v-if="!envelopeFinalized"
        >
        Envelopes in progress
      </router-link>
      
      <router-link
         :to="{name:'EnvelopesArchive', params: {reporterId: `${$route.params.reporterId}`}}"
         v-else
        >
        Envelopes archive
      </router-link>
      <span class="separator">/</span>
      
      <router-link
         :to="{name:'EnvelopeDetail', params: {reporterId: `${$route.params.reporterId}`, envelopeId: `${$route.params.envelopeId}`}}"

        >
        {{envelopeName}}
      </router-link>
      <span class="separator">/</span>
      <span class="current-page">{{file.name}}</span>
    </div>
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
            <div>{{formatSize(file.size)}}</div>
          </div>
          <div class="file-details-section">
            <label>Last modified</label>
            <div>{{formatDate(file.updated, 5)}}</div>
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
          <div>{{fileQaScripts.length}} tests<b-btn @click="runAllQAScripts" variant="link"> Run all tests</b-btn></div>
          <div  class="qa-tests">
            <div
              style="display: flex; justify-content: space-between"
              class="mb-2"
              v-for="script in fileQaScripts"
              :key="script.id">
              <a :href='`#${script.id}`'>
                {{script.title}}
              </a>
              <b-btn
                variant="primary"
                class="test-button"
                v-on:click.stop="runQAScript(file, script.id, $event)"
                >
                Run test
              </b-btn>
            </div>
          </div>
        </div>
      </b-col>
    </b-row>

     <b-modal v-if="modalFile" id="downloadModal" ref="downloadModal" size="lg" title="Download">
          <filesdownload :files="modalFile"></filesdownload>
    </b-modal>
    <div 
      v-if="testResult" 
      v-for="result in testResult"
      :key="result.id"
    >
      <div
        v-if="result.data"
        :id="result.id"
        v-html="result.data"
        class="testResult"
      >
      </div>
    </div>
    <backtotop text="Back to top"></backtotop>

  </div>
</template>

<script>
import {
  fetchEnvelope,
  fetchEnvelopeFile,
  updateFile,
  updateFileRestriction,
  removeFile,
  fetchEnvelopeFilesQAScripts,
  runEnvelopeFilesQAScript
} from '../api';
import utilsMixin from '../mixins/utils.js';
import EnvelopeFilesDownload from './EnvelopeFilesDownload';
import BackToTop from 'vue-backtotop';

export default {
  name: 'FileDetails',

  mixins: [utilsMixin],

  data() {
    return {
      file: null,
      modalFile: [], // will only contain the current file, needs to be array for reusing EnvelopeFilesDownload
      envelopeName: null,
      fileQaScripts: null,
      isEditing: false,
      envelopeFinalized: false,
      testResult: [],
    };
  },

  components: {
    filesdownload: EnvelopeFilesDownload,
    backtotop: BackToTop,
  },

  // Fetches posts when the component is created.
  created() {
    this.getFile();
    this.handleSubscription();
  },

  beforeRouteLeave(to, from, next) {
    this.unsubscribe(`file${this.$route.params.fileId}`);
    next();
  },

  methods: {
    getFile() {
      this.testResult = [];
      this.modalFile = [];
      
      fetchEnvelopeFile(this.$route.params.envelopeId, this.$route.params.fileId)
        .then(response => {
          this.file = response.data;
          this.modalFile.push(this.createModalFile(response.data));

          fetchEnvelopeFilesQAScripts(this.$route.params.envelopeId, this.$route.params.fileId)
            .then(response => {
              let scripts = response.data;
              for (let script of scripts) {
                script.status = null;
                this.testResult.push({ id: script.id, data: null });
              }
              this.fileQaScripts = scripts;
            })
            .catch(error => {
              console.log(error);
            });
        })
        .catch(error => {
          console.log(error);
        });
      fetchEnvelope(this.$route.params.envelopeId)
        .then(response => {
          this.envelopeName = response.data.name;
          this.envelopeFinalized = response.data.finalized;
        })
        .catch(error => {
          console.log(error);
        });
    },

    handleSubscription() {
      const envelopeChannel = `/ws/envelopes/` + this.$route.params.envelopeId;
      const self = this;
      const observer = {
        next(newMessage) {
          self.handleNewMessage(newMessage);
        },
        error(error) {
          console.error('File got an error: ', error);
        },
        complete() {
          console.log('File got a complete notification');
        }
      };

      this.$listen(envelopeChannel);
      this.subscribe(observer, `file${this.$route.params.fileId}`);
    },

    handleNewMessage(newMessage) {
      console.log('File got a next value: ', newMessage);
      if (newMessage.event === 'changed_file' && newMessage.data.file_id.toString() === this.$route.params.fileId) {
        this.getFile();
      }
    },

    runAllQAScripts() {
      for (let script of this.fileQaScripts) {
        this.runQAScript(this.file, script.id);
      }
    },

    runQAScript(file, scriptId, e) {
      if (e) {
        e.target.innerText = 'Running test';
        e.target.setAttribute('disabled', 'true');
      } else {
        document
          .querySelectorAll('.test-button')
          .forEach(function(item, index) {
            item.innerText = 'Running test';
            item.setAttribute('disabled', 'true');
          });
      }

      runEnvelopeFilesQAScript(this.$route.params.envelopeId, file.id, scriptId)
        .then(response => {
          this.fileQaScripts.map(script => {
            if (script.id === scriptId) {
              script.variant = this.envelopeCodeDictionary(response.data.feedback_status);
              this.handleEnvelopeFeedback(response.data.result, scriptId);
            }
            if (e) {
              e.target.innerText = 'Run test';
              e.target.removeAttribute('disabled');
            } else {
              document
                .querySelectorAll('.test-button')
                .forEach(function(item, index) {
                  item.innerText = 'Run test';
                  item.removeAttribute('disabled');
                });
            }
            return script;
          });
        })
        .catch(error => {
          console.log(error);
        });
    },

    handleEnvelopeFeedback(result, scriptId) {
      let matchScript;
      let matchLink;
      let resultObject = {};

      let p = document.createElement('script');
      const re = /<script\b[^>]*>([\s\S]*?)<\/script>/gm;
      const linkRe = /<link href\s*=\s*(['"])(https?:\/\/.+?)\1/gi;

      p.setAttribute('type', 'text/javascript');

      while ((matchScript = re.exec(result))) {
        // full match is in match[0], whereas captured groups are in ...[1], ...[2], etc.
        p.innerHTML += matchScript[1];
      }
      let links = [];
      while ((matchLink = linkRe.exec(result))) {
        links.push(matchLink[2]);
      }
      for (let link of links) {
        result = result.replace(link, ' ');
      }

      document.body.appendChild(p);

      resultObject = { id: scriptId, data: result };

      for (let test of this.testResult) {
        if (test.id === scriptId) {
          test.data = result;
        }
      }
    },

    restricFile(restriction) {
      updateFileRestriction(
        this.$route.params.envelopeId,
        this.file.id,
        restriction
      );
    },

    deleteFile() {
      removeFile(this.$route.params.envelopeId, this.$route.params.fileId)
        .then(response => {
          this.$router.push({
            name: 'EnvelopeDetail',
            params: {
              reporterId: this.$route.params.reporterId,
              envelopeId: this.$route.params.envelopeId
            }
          });
        })
        .catch(error => {
          console.log(error);
        });
    },

    showModal() {
      this.$refs.downloadModal.show();
    },

    createModalFile(data) {
      const file = Object.assign({}, data, {
        availableConversions: [],
        selectedConversion: null
      });
      return file;
    },

    renameFile() {
      this.isEditing = true;
    },

    updateFile() {
      updateFile(this.$route.params.envelopeId, this.file.id, this.file.name);
      this.isEditing = false;
    }
  }
};
</script>

<style lang="scss" scoped>
.file-details {
  background: url("../../img/file-background.svg");
  background-repeat: no-repeat;
  background-size: cover;
  min-height: 386px;
  padding: 1rem;
  max-width: 320px;
  max-height: 400px;
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
    padding: 0.5rem 1.5rem;
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
    font-size: 0.8rem;
    color: #757575;
  }
}

.file-actions {
  a {
    padding: 0.375rem 0.75rem;
  }
  .btn-link {
    font-size: 16px !important;
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
  .testResult {
    overflow: auto;
    box-shadow: 1px 1px 3px #aaa;
    padding: 1rem;
    margin-top: 1rem;
  }
}
</style>
