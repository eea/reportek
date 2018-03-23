<template>
  <div class="envelope-detail">
    <div class="row" v-if="envelope">
      <div class="breadcrumbs">
        <router-link
           :to="{name:'Dashboard', params: {reporterId: `${$route.params.reporterId}`}}"
          >
          Dashboard
        </router-link>
        <span class="separator">/</span>
        <router-link
           :to="{name:'EnvelopesWIP', params: {reporterId: `${$route.params.reporterId}`}}"
           v-if="!envelope.finalized"
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
        <span class="current-page">{{envelope.name}}</span>
      </div>
      <h1 class="envelope-title">{{envelope.name}}
        <b-badge pill class="small" variant="warning">
          <strong>{{translateCode(envelope.workflow.current_state)}}</strong>
        </b-badge>
      </h1>
      <div class="col-lg-9 col-md-9 col-sm-10">

        <workflow :state="envelope.workflow.current_state"></workflow>

        <h4 class="inline"><strong>Envelope files</strong></h4> <small>{{envelope.files.length}} files</small>

        <b-tabs v-model="tabIndex">

          <b-tab title="all" active>

            <b-table
              stacked="md"
              class="files-table"
              border-variant="default"
              :hover="false"
              v-if="envelope.files.length"
              :items="envelope.files"
              @head-clicked="selectAll()"
              :fields="fields"
              :current-page="currentPage"
              :per-page="perPage"
            >
            <div
              slot="HEAD_select"
              slot-scope="row"
            >
              <b-form-checkbox
                v-model="allFilesSelected"
              >
              </b-form-checkbox>
              <span style="position: absolute;
                    left: 3rem;
                    top: 1rem;
                    white-space: nowrap;"
              >
                Select All
              </span>
            </div>

              <div
                slot="name"
                slot-scope="row"
              >
                <b-form-input
                  type="text"
                  v-model="row.item.name"
                  v-if="row.item.isEditing"
                >
                </b-form-input>

                <div class="blue-color" v-if="!row.item.isEditing">
                  <router-link
                    :to="{name:'FileDetails', params: {envelopeId: `${envelope.id}`, fileId: `${row.item.id}`}}"
                  >
                  {{row.item.name}}
                  </router-link>

                </div>
                <div>
                  <small class="muted">XML document, {{formatSize(row.item.size)}}</small>
                </div>

                <div class="file-tests">
                  <b-button
                    v-for="script in row.item.availableScripts"
                    :key="script.data.id"
                    :variant="script.variant"
                    v-on:click.stop="runQAScript(row.item, script.data.id)"
                    v-show="row.item.visibleScripts"
                  >
                    {{script.data.title}}
                  </b-button>
                </div>

              </div>

              <div
                slot="tests"
                slot-scope="row"
                class="card-link"
                style="text-align: right;"
              >

                  <div class="test-trigger">
                    <b-btn
                      variant="link"
                      class="muted"
                      v-on:click="getFileScripts(row.item)"
                      v-show="row.item.visibleScripts === false"
                    >
                      <i class="far fa-plus-square"></i> View Tests
                    </b-btn>
                    <b-btn
                      variant="link"
                      class="muted"
                      v-show="row.item.visibleScripts === true"
                      v-on:click="row.item.visibleScripts = false"
                    >
                      <i class="far fa-minus-square"></i> Hide Tests
                    </b-btn>
                  </div>

                <span class="more-actions-control">
                  <b-btn
                    @click="row.item.additionalControls = toggleAdditionalControls(row.item.additionalControls)"
                    variant="link"
                    class="muted"
                  >
                    <i class="fas fa-bars"></i>
                  </b-btn>
                </span>
                <div
                  class="more-actions"
                  style="
                    display: flex;
                    text-align: right;
                    flex-direction: column;
                    align-items: flex-end;"
                  v-show="row.item.additionalControls">
                  <b-btn
                    variant="link"
                    v-on:click="renameFile(row.item)"
                    v-if="!row.item.isEditing"
                  >
                    Rename File
                  </b-btn>
                  <b-btn
                    variant="link"
                    v-on:click="updateFile(row.item)"
                    v-if="row.item.isEditing"
                  >
                    Save File
                  </b-btn>
                </div>

              </div>

              <b-form-checkbox
                slot="select"
                slot-scope="row"
                @change="selectFile(row.item, $event)"
                v-model="row.item.selected">
              </b-form-checkbox>
            </b-table>

            <b-card
              title="Work area empty"
              class="empty-workarea"
              v-else
            >
              <p>Start uploading files so you can test them and prepare for delivery</p>

              <form
                enctype="multipart/form-data"
                novalidate
                class="upload-form"
              >
                <label
                  :class="[ {'disabled': filesUploading || !envelope.workflow.upload_allowed  }, 'btn', 'btn-primary']"
                  for="file_uploads"
                >
                  <i class="far fa-folder-open"></i>  Upload files
                </label>
                <input
                  type="file"
                  id="file_uploads"
                  class="hidden-input"
                  :disabled="filesUploading || !envelope.workflow.upload_allowed"
                  v-on:change="onFileChange"
                  multiple
                >
              </form>

            </b-card>

            <b-pagination
              :total-rows="envelope.files.length"
              :per-page="perPage"
              v-model="currentPage"
              v-if="envelope.files.length > 5"
              class="my-0"
            />
          </b-tab>

          <b-tab title="feedback">
            <br>
            <div v-if="envelopeFeedback">
              <b-jumbotron
                :header="key"
                bg-variant="white"
                border-variant="default"
                class="feedback-container"
                v-for="(file, key) in envelopeFeedback.files"
                :key="file.id"
              >
                <span
                  v-for="feedback in file"
                  v-html="feedback.latest_result.value"
                  :key="feedback.id"
                >
                </span>
              </b-jumbotron>
            </div>
          </b-tab>

          <b-tab v-for="tab in extraTabs" :key="tab" :title="tab">
            <b-list-group>
              <b-list-group-item
                v-for="file in files"
                :key="file.data.name"
              >
                <div class="file-row">
                  <span>{{file.data.name}}</span>
                  <b-btn @click="removeFileFromUploadList(file)" variant="danger"> Remove file </b-btn>
                </div>

                <b-progress-bar
                  :value="file.percentage"
                  :max="max"
                  show-progress
                  animated
                >
                </b-progress-bar>
              </b-list-group-item>
            </b-list-group>
          </b-tab>

        </b-tabs>

    </div>
    <div class="col-lg-3 col-md-3 col-sm-10">
        <div class="sidebar-item">
          <div class="file-control">
            <div class="file-control-header">
              <span class="blue-color">
                <i class="fas fa-file"></i>
              </span>
              {{selectedFiles}} files selected
            </div>

            <div class="file-control-body">
              <b-button
                v-show="selectedFiles"
                @click="showModal"
                variant="white sidebar-button"
              >
                <i class="far fa-folder-open"></i>
                Download
              </b-button>

              <b-button
                v-show="selectedFiles"
                variant="white sidebar-button"
                v-on:click="runScriptsForFiles"
              >
                <i class="fas fa-play"></i>
                Run tests
              </b-button>

              <b-button
                v-show="selectedFiles"
                v-on:click="deleteFiles"
                variant="white sidebar-button"
              >
                <i class="far fa-trash-alt"></i>
                Delete
              </b-button>

            <form
              enctype="multipart/form-data"
              novalidate
              class="upload-form">
                  <label
                    :class="[ {'disabled': filesUploading || !envelope.workflow.upload_allowed }, 'btn', 'btn-white', 'sidebar-button']"
                    for="file_uploads"
                  >
                    <i class="far fa-folder-open"></i>
                    Upload files
                  </label>
                  <input
                    type="file"
                    id="file_uploads"
                    class="hidden-input"
                    :disabled="filesUploading || !envelope.workflow.upload_allowed"
                    v-on:change="onFileChange"
                    multiple
                  >
            </form>

            <b-button
                variant="primary sidebar-button"
                v-on:click="uploadAllFiles"
                :disabled="!envelope.workflow.upload_allowed || filesUploading"
                v-show = "files.length"
              >
                <i class="fas fa-play"></i> Add files to envelope
            </b-button>
            </div>
          </div>
        </div>

        <div class="sidebar-item">
          <div class="status-control">
            <div class="status-control-header yellow-bg">
              Envelope status: {{translateCode(envelope.workflow.current_state)}}
            </div>
           <div class="status-control-body">
            <div>{{envelope.files.length}} files uploaded</div>
            <p  v-if="translateCode(envelope.workflow.current_state) === 'Draft'" class="">
              Add files and run QA tests on them. Fix any error you encounter and keep adding files.
              When the envelope is ready run all tests and get feedback
            </p>
            <p v-else class="">
              Envelope is in transition
            </p>

            <div style="text-align: center;">
              <b-button
                v-for="transition in envelope.workflow.available_transitions"
                :key="transition"
                v-if="showTransitionButton(transition)"
                variant="primary"
                v-on:click="goToTransition($event, transition)"
              >
                {{translateCode(transition)}}
              </b-button>
            </div>
           </div>

          </div>
        </div>
        <!-- Modal Component -->
        <b-modal id="downloadModal" ref="downloadModal" size="lg" title="Download">
          <filesdownload :files="modalFiles()"></filesdownload>
        </b-modal>
    </div>
  </div>
  </div>
</template>

<script>
import History from './EnvelopeHistory';
import Workflow from './EnvelopeWorkflow';
import EnvelopeFilesDownload from './EnvelopeFilesDownload';
import {
  fetchEnvelope,
  fetchEnvelopeToken,
  fetchEnvelopeFeedback,
  fetchEnvelopeFilesQAScripts,
  runEnvelopeFilesQAScript,
  fetchEnvelopeFiles,
  runEnvelopeTransition,
  updateFile,
  removeFile,
  uploadFile
} from '../api';
import utilsMixin from '../mixins/utils.js';


export default {
  name: 'EnvelopeDetail',

  components: {
    history: History,
    workflow: Workflow,
    filesdownload: EnvelopeFilesDownload,
  },

  mixins: [utilsMixin],

  data() {
    return {
      fields: ['select', 'name', 'tests'],
      envelope: null,
      allFilesSelected: false,
      selectedFiles: 0,
      envelopeState: '',
      isInitial: true,
      files: [],
      envelopeFeedback: null,
      max: 100,
      currentPage: 1,
      perPage: 5,
      extraTabs: [],
      tabIndex: 0,
      filesUploading: false,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.handleSubscription();

    this.getEnvelope().then(resultFiles => {
      this.getEnvelopeFeedback(resultFiles);
    });
  },

  destroyed() {
    // TODO solve multiple event for reentering the same envelope
    this.unsubscribe();
  },

  methods: {

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
      this.subscribe(observer);
    },

    handleNewMessage(newMessage) {
      console.log('File got a next value: ', newMessage);
      this.getEnvelope().then(resultFiles => {
        this.getEnvelopeFeedback(resultFiles);
      });
    },

    getEnvelope() {
      return new Promise((resolve, reject) => {
        fetchEnvelope(this.$route.params.envelopeId)
          .then(response => {
            // JSON responses are automatically parsed.
            this.envelope = response.data;
            this.envelopeState = this.envelopeCodeDictionary(
              response.data.workflow.available_transitions[0]
            );

            for (let index = 0; index < this.envelope.files.length; index += 1) {
              this.envelope.files[index] = Object.assign({}, this.envelope.files[index],
                {
                  availableScripts: [],
                  selected: false,
                  visibleScripts: false,
                  availableConversions: [],
                  selectedConversion: null,
                  feedback: [],
                  isEditing: false,
                  additionalControls: false,
                }
              );
            }
            resolve(this.envelope.files);
          })
          .catch(error => {
            console.log(error);
            reject(error);
          });
      });
    },

    getEnvelopeFeedback(files) {
      this.envelopeFeedback = null;
      fetchEnvelopeFeedback(this.$route.params.envelopeId).then(response => {
        this.handleEnvelopeFeedback(response.data, files);
      });
    },

    handleEnvelopeFeedback(feedback, files) {
      let matchScript;
      let matchLink;
      let modifiedFeedback = {
        auto_qa_completed: feedback.auto_qa_completed,
        auto_qa_ok: feedback.auto_qa_ok,
        count: feedback.count,
        next: feedback.next,
        previous: feedback.previous,
        files: {},
      };
      let p = document.createElement('script');
      const re = /<script\b[^>]*>([\s\S]*?)<\/script>/gm;
      const linkRe = /<link href\s*=\s*(['"])(https?:\/\/.+?)\1/gi;

      p.setAttribute('type', 'text/javascript');

      for (let file of files) {
        modifiedFeedback.files[file.name] = [];
      }

      for (let result of feedback.results) {
        while ((matchScript = re.exec(result.latest_result.value))) {
          // full match is in match[0], whereas captured groups are in ...[1], ...[2], etc.
          p.innerHTML += matchScript[1];
        }
        let links = [];
        while ((matchLink = linkRe.exec(result.latest_result.value))) {
          links.push(matchLink[2]);
        }
        for (let link of links) {
          result.latest_result.value = result.latest_result.value.replace(link, ' ');
        }
        for (let file of files) {
          if (file.id === result.envelope_file) {
            modifiedFeedback.files[file.name].push(result);
          }
        }
      }

      document.body.appendChild(p);
      this.envelopeFeedback = modifiedFeedback;
    },

    onFileChange(e) {
      const newfiles = e.target.files;

      for (const file of newfiles) {
        this.files.push({ data: file, percentage: 0 });
      }
      if (this.extraTabs.length === 0) {
        this.extraTabs.push('New Files');
      }
      setTimeout(() => {
        this.tabIndex = 2;
      });
    },

    uploadAllFiles(e) {
      // e.preventDefault();
      this.filesUploading = true;

      // for each file create a function that returns a promise
      const funcs = this.files.map(file => () => this.uploadFile(file));

      // reduce the array or functions that return promises, in a chain
      const promiseSerial = functions =>
        functions.reduce(
          (promise, func) =>
            promise.then(resultPromise =>
              func().then(resultFunc => {
                // this.updateFilesList();
              })
            ),
          Promise.resolve([])
        );

      // execute Promises in serial, clear files at the end of all promisees
      promiseSerial(funcs)
        .then(() => {
          this.files = [];
          this.extraTabs = [];
          this.tabIndex = 0;
          this.filesUploading = false;
        })
        .catch(console.error.bind(console));
    },

    uploadFile(file) {
      // Create a new tus upload
      return new Promise((resolve, reject) => {
        fetchEnvelopeToken(this.$route.params.envelopeId)
          .then(response => {
            return uploadFile(
              file,
              file.data.name,
              file.data.id,
              response.data.token
            );
          })
          .then(response => {
            resolve(response);
          })
          .catch(error => {
            console.log(error);
            this.handleUploadFileError(file);
          });
      });
    },

    handleUploadFileError(file) {
      this.filesUploading = false;
      this.removeFileFromUploadList(file);
      this.uploadAllFiles();
      alert('file type is wrong. It will be removed');
    },

    removeFileFromUploadList(file) {
      this.files.splice(this.files.indexOf(file), 1);
    },

    runScriptsForFiles() {
      this.envelope.files.map(file => {
        if (file.selected) {
          this.getFileScripts(file)
            .then(response => {
              response.availableScripts.map(script => {
                this.runQAScript(response, script.data.id);
              });
            })
            .catch(error => {
              console.log(error);
            });
        }
      });
    },

    getFileScripts(file) {
      return new Promise((resolve, reject) => {
        if (file.availableScripts.length === 0) {
          fetchEnvelopeFilesQAScripts(this.$route.params.envelopeId, file.id)
            .then(response => {
              file.visibleScripts = true;
              response.data.map(script => {
                file.availableScripts.push({ data: script, variant: 'primary' });
                return script;
              });
              resolve(file);
            })
            .catch(error => {
              console.log(error);
              reject(error);
            });
        } else {
          resolve(file);
          file.visibleScripts = true;
        }
      });
    },

    runQAScript(file, scriptId) {
      runEnvelopeFilesQAScript(this.$route.params.envelopeId, file.id, scriptId)
        .then(response => {
          file.availableScripts.map(script => {
            if (script.data.id === scriptId) {
              script.variant = this.envelopeCodeDictionary(response.data.feedback_status);
            }
            return script;
          });
        })
        .catch(error => {
          console.log(error);
        });
    },

    showModal() {
      this.modalFiles();
      this.$refs.downloadModal.show();
    },

    modalFiles() {
      let files = [];

      for (let file of this.envelope.files) {
        if (file.selected) {
          files.push(file);
        }
      }
      return files;
    },

    selectFile(file, value) {
      file.selected = value;

      if (value === false) {
        this.allFilesSelected = false;
        this.selectedFiles -= 1;
      } else {
        this.selectedFiles += 1;
        if (this.selectedFiles === this.envelope.files.length) {
          this.allFilesSelected = true;
        }
      }
    },

    selectAll() {
      if (this.allFilesSelected === true) {
        for (const file of this.envelope.files) {
          file.selected = false;
        }
        this.selectedFiles = 0;
        this.allFilesSelected = false;
      } else {
        for (const file of this.envelope.files) {
          file.selected = true;
          this.selectedFiles += 1;
        }
        this.allFilesSelected = true;
      }
    },

    toggleAdditionalControls(state) {
      return !state;
    },

    renameFile(file) {
      file.isEditing = true;
    },

    updateFile(file) {
      updateFile(this.$route.params.envelopeId, file.id, file.name)
        .then(response => {
          this.getEnvelope().then(resultFiles => {
            this.getEnvelopeFeedback(resultFiles);
          });
        })
        .catch(error => {
          console.log(error);
        });
    },

    deleteFiles() {
      this.envelope.files.map(file => {
        if (file.selected) {
          this.deleteFile(file);
        }
      });
    },

    pushUnique(array, item) {
      if (array.indexOf(item) === -1) {
        array.push(item);
      }
    },

    deleteFile(file) {
      removeFile(this.$route.params.envelopeId, file.id)
        .then(response => {
          this.getEnvelope().then(resultFiles => {
            this.getEnvelopeFeedback(resultFiles);
          });
        })
        .catch(error => {
          console.log(error);
        });
    },

    goToTransition(e, transition) {
      e.preventDefault();

      runEnvelopeTransition(this.$route.params.envelopeId, transition);
    },

    showTransitionButton(code) {
      return code !== 'fail_qa' && code !== 'pass_qa';
    }
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss">
.sidebar-item {
  margin-top: 1rem;
  padding-top: 1rem;
}
.envelope-title {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
  border-bottom: 1px solid #eee;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  padding-top: 1rem;
  .badge {
    font-size: 1rem;
    font-weight: normal;
    margin: 1rem;
    min-width: 60px;
  }
}
.absolute-right {
  position: absolute;
  right: 15px;
}

.feedback-container {
  overflow-x: auto;
  h1 {
    margin-bottom: 2rem;
  }
}
.upload-form {
  position: relative;
  .hidden-input {
    opacity: 0;
    position: absolute;
    left: 0;
    z-index: -1;
  }
  label {
    cursor: pointer;
  }
}

.status-control {
  border-radius: 4px;
  border: 1px solid #eee;
  p {
    font-size: 0.8rem;
    font-style: italic;
    color: rgba(0, 0, 0, 0.54);
  }
  .status-control-header {
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    text-align: center;
    padding: 0.3rem;
    font-weight: 600;
  }
  .status-control-body {
    padding: 1rem;
  }
}

.files-table {
  thead {
    th:not(:first-of-type) {
      display: none;
    }
    th:first-of-type {
      // white-space: nowrap;
    }
    th {
      border: none;
      padding-left: 0;
    }
  }
  td {
    padding: 1rem 0 1rem 0;
    vertical-align: middle;
  }
  td[data-label="Select"] {
    width: 1px;
  }
  button,
  a,
  label {
    cursor: pointer;
  }
  .btn {
    font-size: initial;
  }
  .btn-link:hover {
    text-decoration: none;
  }
}
.file-control {
  .file-control-body {
    button {
      margin-bottom: 5px;
      height: 36px;
    }
  }
  .file-control-header {
    border-bottom: 1px solid #eee;
    margin-bottom: 1rem;
    padding-bottom: 0.3rem;
    padding-left: 1rem;
  }
}

.empty-workarea {
  margin-top: 2rem;
  text-align: center;
  .card-title {
    font-weight: bold;
  }
}

label.disabled {
  color: grey;
}

.more-actions-control,
.test-trigger {
  display: inline-block;
}

.more-actions {
  button {
    display: block;
  }
}

.file-row {
  display: flex;
  justify-content: space-between;
  width: 100%;
}
</style>
