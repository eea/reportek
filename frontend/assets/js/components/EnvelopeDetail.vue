<template>
  <div class="hello">
    <div class="row" v-if="envelope">
      <div class="col-lg-8 col-md-8 col-sm-10">
        <h1 class="envelope-title">{{envelope.name}} <b-badge pill class="small" variant="primary">{{translateCode(envelope.workflow.current_state)}}</b-badge></h1>


        <b-jumbotron
            bg-variant="white"
            border-variant="default"
            class="status-control"
            :header="translateCode(envelope.workflow.current_state)"
          >
         <div class="row">

          <p  v-if="translateCode(envelope.workflow.current_state) === 'Draft'" class="col order-1">
            Add files and run QA tests on them. Fix any error you encounter and keep adding files.
            When the envelope is ready run all tests and get feedback
          </p>
          <p v-else class="col order-1">
            Envelope is in transition
          </p>

          <div class="col-lg-3 col-sm-5 col-md-3 order-2 d-flex align-items-start justify-content-center">
            <b-button
                v-for="transition in envelope.workflow.available_transitions"
                :key="transition"
                v-if="showTransitionButton(transition)"
                variant="primary"
                v-on:click="goToTransition($event, transition)">
                  {{translateCode(transition)}}
              </b-button>
          </div>
         </div>

        </b-jumbotron>



        <p><strong>Envelope files {{envelope.files.length}}</strong></p>

        <b-button
          variant="primary"
          v-on:click="uploadAllFiles"
          :disabled="!envelope.workflow.upload_allowed"
          class="absolute-right"
        >
            Upload Files
        </b-button>

        <b-tabs>
          <b-tab title="all" active>
            <br>All

            <b-table
              stacked="md"
              border-variant="default"
              :hover="false"
              :items="envelope.files"
              :fields="fields"
              :current-page="currentPage"
              :per-page="perPage"
            >

              <div
                slot="name"
                slot-scope="row"
              >
                <b-form-input
                  type="text"
                  v-model="row.item.name"
                  v-if="row.item.isEditing"
                ></b-form-input>
                <p v-if="!row.item.isEditing">
                  {{row.item.name}}
                </p>

              </div>

              <div
                slot="file"
                slot-scope="row"
              >

                <b-link
                  href="#"
                  class="card-link"
                  v-on:click="renameFile(row.item)"
                  v-if="!row.item.isEditing"
                >
                  <p>Rename File</p>
                </b-link>

                <b-link
                  href="#"
                  class="card-link"
                  v-on:click="updateFile(row.item)"
                  v-if="row.item.isEditing"
                >
                  <p>Save File</p>
                </b-link>

                <b-link
                  href="#"
                  class="card-link"
                  v-on:click="deleteFile(row.item)"
                >
                  <p>Delete File</p>
                </b-link>
              </div>

              <b-link
                href="#"
                class="card-link"
                slot="tests"
                slot-scope="row"
                v-on:click="getFileScripts(row.item)"
              >

                <b-button
                  v-for="script in row.item.availableScripts"
                  :key="script.data.id"
                  :variant="script.variant"
                  v-on:click.stop="runQAScript(row.item, script.data.id)"
                >
                    {{script.data.title}}
                </b-button>

                <p v-show="row.item.availableScripts.length === 0">Run a test</p>
              </b-link>

              <div
                slot="convert"
                slot-scope="row"
              >

                <b-link
                  href="#"
                  class="card-link"
                  v-on:click.stop="getFileConversions(row.item)"
                  v-show="row.item.availableConversions.length === 0"
                >
                  <p>Choose Conversion</p>
                </b-link>

                <b-link
                  href="#"
                  class="card-link"
                  v-on:click="convertScript(row.item)"
                  v-show="row.item.availableConversions.length > 1"
                >
                  <p>Convert</p>
                </b-link>

                <b-form-select
                  :options="row.item.availableConversions"
                  v-model="row.item.selectedConversion"
                  v-show="row.item.availableConversions.length > 1"
                >
                </b-form-select>
                <p v-show="row.item.availableConversions.length === 1">No conversions available</p>

              </div>

              <b-form-checkbox
                slot="select"
                slot-scope="row"
                v-model="row.selected">
              </b-form-checkbox>
            </b-table>

            <b-pagination
              :total-rows="envelope.files.length"
              :per-page="perPage"
              v-model="currentPage"
              v-if="envelope.files.length > 5"
              class="my-0"
            />

            <form
              enctype="multipart/form-data"
              novalidate v-if="isInitial || isSaving"
              class="upload-form">
                  <label for="file_uploads">Add files to envelope</label>
                  <input
                    type="file"
                    id="file_uploads"
                    class="hidden-input"
                    v-on:disabled="isSaving"
                    v-on:change="onFileChange"
                    multiple
                  >
            </form>

            <b-list-group>
              <b-list-group-item
                v-for="file in files"
                :key="file.data.name"
              >
                {{file.data.name}}

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
        </b-tabs>

    </div>
    <div class="col-lg-4 col-md-4 col-sm-10">
        <div class="sidebar-item">
        <h5>Details</h5>
          <p>Reporting on obligation {{envelope.obligation_spec}} in cycle {{envelope.reporting_cycle}}</p>
          <b-link href="#" class="card-link">Edit Envelope</b-link>
        </div>
        <history :created_at="envelope.created_at"></history>
      </div>
  </div>
  </div>
</template>

<script>
import tus from 'tus-js-client';
import History from './EnvelopeHistory';
import { fetchEnvelope,
          fetchEnvelopeToken,
          fetchEnvelopeFeedback,
          fetchEnvelopeFilesQAScripts,
          runEnvelopeFilesQAScript,
          fetchEnvelopeFiles,
          runEnvelopeTransition,
          fetchEnvelopeFilesConvertScripts,
          runEnvelopeFilesConvertScript,
          updateFile,
          removeFile,
          } from '../api';
import { dateFormat } from '../utils/UtilityFunctions';


const envelopeCodeDictionary = (status) => {
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
  if (!status) return '';
  return codeDictionary[status.trim().toLowerCase()] || status;
};

export default {
  name: 'EnvelopeDetail',
  components: {
    history: History,
  },


  data() {
    return {
      fields: ['select', 'name', 'file', 'tests', 'convert'],
      envelope: null,
      envelopeState: '',
      isSaving: false,
      isInitial: true,
      files: [],
      envelopeFeedback: null,
      max: 100,
      currentPage: 1,
      perPage: 5,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.getEnvelope()
      .then((resultFiles) => {
        this.getEnvelopeFeedback(resultFiles);
      });

  },

  methods: {
    getEnvelope() {
      return new Promise((resolve, reject) => {
        fetchEnvelope(this.$route.params.envelope_id)
          .then((response) => {
            // JSON responses are automatically parsed.
            this.envelope = response.data;
            this.envelopeState = envelopeCodeDictionary(response.data.workflow.available_transitions[0]);

            for (let index = 0; index < this.envelope.files.length; index += 1) {
              this.envelope.files[index] = Object.assign(
                {},
                this.envelope.files[index],
                {
                  availableScripts: [],
                  availableConversions: [],
                  selectedConversion: null,
                  feedback: [],
                  isEditing: false,
                });
            }
            resolve(this.envelope.files);
          })
          .catch((e) => {
            reject(e);
            console.log(e);
          });
      });
    },

    getEnvelopeFeedback(files) {
      this.envelopeFeedback = null;
      fetchEnvelopeFeedback(this.$route.params.envelope_id)
        .then((response) => {
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
      }

      let p = document.createElement("script");
      const re = /<script\b[^>]*>([\s\S]*?)<\/script>/gm;
      const link_re = /<link href\s*=\s*(['"])(https?:\/\/.+?)\1/ig;

      p.setAttribute("type", "text/javascript");

      for (let file of files) {
        modifiedFeedback.files[file.name] = []
      }

      for (let result of feedback.results){
        while (matchScript = re.exec(result.latest_result.value)) {
          // full match is in match[0], whereas captured groups are in ...[1], ...[2], etc.
          p.innerHTML += matchScript[1];
        }
        let links = []
        while (matchLink = link_re.exec(result.latest_result.value)) {
          links.push(matchLink[2])
        }
        for (let link of links) {
          result.latest_result.value = result.latest_result.value.replace(link, " ")
        }
        for (let file of files){
          if(file.id === result.envelope_file){
            modifiedFeedback.files[file.name].push(result)
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
    },

    uploadAllFiles(e) {
      e.preventDefault();

      // for each file create a function that returns a promise
      const funcs = this.files.map((file) => () => this.uploadFile(file));

      // reduce the array or functions that return promises, in a chain
      const promiseSerial = functions =>
        functions.reduce((promise, func) =>
          promise.then(resultPromise =>
            func().then((resultFunc) => { this.updateFilesList(); }),
          ),
          Promise.resolve([]),
        );

      // execute Promises in serial, clear files at the end of all promisees
      promiseSerial(funcs)
        .then(() => { this.files = []; })
        .catch(console.error.bind(console));
    },

    uploadFile(file) {
      // Create a new tus upload
      return new Promise((resolve, reject) => {
        fetchEnvelopeToken(this.$route.params.envelope_id)
          .then((response) => {
            const token = response.data.token;
            const upload = new tus.Upload(file.data,
              {
                endpoint: 'http://localhost:1080/files/',
                metadata: {
                  token,
                  filename: file.data.name,
                  fileId: file.data.id,
                },
                retryDelays: [0, 1000, 3000, 5000],
                onError: function onError(error) {
                  console.log('Failed because: ', error);
                  reject(error);
                },
                onProgress: function onProgress(bytesUploaded, bytesTotal) {
                  file.percentage = parseInt(((bytesUploaded / bytesTotal) * 100).toFixed(2), 10);
                  console.log(bytesUploaded, bytesTotal, file.percentage, '%');
                },
                onSuccess: function onSuccess() {
                  console.log('Download %s from %s', upload.file.name, upload.url);
                  resolve(
                    {
                      fileName: upload.file.name,
                      uploadUrl: upload.url,
                    },
                  );
                },
              });
            // Start the upload
            upload.start();
          });
      });
    },

    updateFilesList() {
      return this.pollFiles(() => fetchEnvelopeFiles(this.$route.params.envelope_id), 500);
    },

    // TODO if file already exists and will not be added to the server, the poll will request forever
    pollFiles(fn, delay) {
      const self = this;
      setTimeout(() => {
        fn()
          .then((response) => {
            if (self.envelope.files.length === response.data.length) {
              self.pollFiles(fn, delay);
            } else {
              for (let index = 0; index <= response.data.length; index += 1) {
                const responseFile = response.data[index];
                const found = self.envelope.files.find(file => file.id === responseFile.id);

                if (found === undefined) {
                  responseFile.availableScripts = [];
                  responseFile.availableConversions = [];
                  responseFile.isEditing = false;
                  self.envelope.files.push(responseFile);
                  self.files.shift();
                }
              }
            }
          })
          .catch((error) => {
            console.log(error);
          });
      }, delay);
    },

    getFileScripts(file) {
      fetchEnvelopeFilesQAScripts(this.$route.params.envelope_id, file.id)
        .then((response) => {
          response.data.map((script) => {
            file.availableScripts.push({ data: script, variant: 'primary' });
            return script;
          });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    runQAScript(file, scriptId) {
      runEnvelopeFilesQAScript(this.$route.params.envelope_id, file.id, scriptId)
        .then((response) => {
          file.availableScripts.map((script) => {
            if (script.data.id === scriptId) {
              script.variant = envelopeCodeDictionary(response.data.feedback_status);
            }
            return script;
          });
        })
        .catch((error) => {
          console.log(error);
        });
    },

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
            console.log(response.data)
            this.download(response.data, fileName, fileType);
          })
          .catch((error) => {
            console.log(error);
          });
      }
    },

    download(blob, filename, filetype) {
        var a = window.document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([blob], {type: filetype}));
        a.download = filename;

        // Append anchor to body.
        document.body.appendChild(a);
        a.click();

        // Remove anchor from body
        document.body.removeChild(a);
      },

    renameFile(file) {
      file.isEditing = true;
    },

    updateFile(file) {
      updateFile(this.$route.params.envelope_id, file.id, file.name)
        .then((response) => {
          this.getEnvelope()
            .then((resultFiles) => {
              this.getEnvelopeFeedback(resultFiles);
            });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    deleteFile(file) {
      removeFile(this.$route.params.envelope_id, file.id)
        .then((response) => {
          this.getEnvelope()
            .then((resultFiles) => {
              this.getEnvelopeFeedback(resultFiles);
            });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    goToTransition(e, transition) {
      e.preventDefault();

      runEnvelopeTransition(this.$route.params.envelope_id, transition)
        .then((response) => {
          this.getEnvelope(this.$route.params.envelope_id).then((resultFiles) => {
            this.updateFeedback(resultFiles);
          });
        })
        .catch((error) => {
          console.log(error);
        });
    },

    updateFeedback(resultFiles) {
      return this.pollFeedback(() => fetchEnvelopeFeedback(this.$route.params.envelope_id,resultFiles), 10000);
    },

    pollFeedback(fn, delay) {
      const self = this;
      setTimeout(() => {
        fn()
          .then((response) => {
            if (!response.data.auto_qa_completed) {
              self.pollFeedback(fn, delay);
            } else {
                self.getEnvelope()
                .then((resultFiles) => {
                  self.getEnvelopeFeedback(resultFiles);
                })
                .catch((error) => {
                  console.log(error);
                });
            }
          })
          .catch((error) => {
            console.log(error);
          });
      }, delay);
    },

    translateCode(code) {
      return envelopeCodeDictionary(code);
    },

    showTransitionButton(code) {
        return code !== 'fail_qa' && code !== 'pass_qa'
    },

    formatDate(date, count){
      return dateFormat(date,count)
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
.sidebar-item {
  border-top: 1px solid rgba(0,0,0,.15);
  margin-top: 1rem;
  padding-top: 1rem;
}
.envelope-title {
  display: flex;
  justify-content: flex-start;
  align-items: center;
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
    font-size: 2rem;
    margin-bottom: 2rem;
  }
}
.upload-form {
  margin-top: 2rem;
  position: relative;
  .hidden-input {
    opacity: 0;
    position: absolute;
    left: 0;
    z-index: -1;
  }
  label {
    cursor: pointer;
    color: #767676;
    &:before {
      content: "➕";
      border: 1px solid #767676;
      color: inherit;
      border-radius: 10rem;
      padding: .3rem .5rem;
      margin-right: .5rem;
    }
    &:hover {
      color: #444;
    }
  }
}
.status-control {
  padding: 1rem;
  h1 {
    font-size: 1.2rem;
  }
}
</style>
