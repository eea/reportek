<template>
  <div class="hello">
    <div class="row" v-if="envelope">
      <div class="col">
        <!-- <p><strong>Envelope files {{envelope.files.length}}</strong></p> -->

        <b-button
          v-for="transition in envelope.workflow.available_transitions"
          :key="transition"
          variant="success"
          v-on:click="goToTransition($event, transition)">
            {{translateCode(transition)}}
        </b-button>

        <b-button
          variant="success"
          v-on:click="uploadAllFiles"
          :disabled="!envelope.workflow.upload_allowed"
        >
            Upload Files
        </b-button>

        <b-tabs>
          <b-tab title="all" active>
            <br>All

            <b-table
              :hover="false"
              :items="envelope.files"
              :fields="fields"
            >

              <a
                slot="file"
                slot-scope="row"
                v-bind:href="row.value"
              >
                Edit File
              </a>

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

              <b-form-checkbox
                slot="select"
                slot-scope="row"
                v-model="row.selected">
              </b-form-checkbox>
            </b-table>

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
          <b-tab title="restricted">
            <br>Restricted from public
          </b-tab>
          <b-tab title="public">
            <br>Public
          </b-tab>
          <b-tab title="feedback">
            <br>
            {{envelopeFeedback}}
          </b-tab>
        </b-tabs>

        <form
          enctype="multipart/form-data"
          novalidate v-if="isInitial || isSaving">
            <label for="file_uploads">Add files to envelope</label>
            <input
              type="file"
              id="file_uploads"
              v-on:disabled="isSaving"
              v-on:change="onFileChange"
              multiple
            >
        </form>
    </div>
    <div class="col-4">
        <div class="sidebar-item">
        <h5>Details</h5>
          <p><strong>name: {{envelope.name}}</strong></p>
          <p>country: {{envelope.country}}</p>
          <p>reporting_period: {{envelope.reporting_cycle}}</p>
          <p>reporting_period: {{envelope.created_at.end}}</p>
          <p>current_state: {{translateCode(envelope.workflow.current_state)}}</p>
          <p>previous_state: {{translateCode(envelope.workflow.previous_state)}}</p>
          <p>upload_allowed: {{envelope.workflow.upload_allowed}}</p>
          <p>created_at: {{envelope.created_at}}</p>
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
          } from '../api';

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
  name: 'EnvelopeItem',
  components: {
    history: History,
  },

  data() {
    return {
      fields: ['select', 'name', 'file', 'tests'],
      envelope: null,
      envelopeState: '',
      isSaving: false,
      isInitial: true,
      files: [],
      envelopeFeedback: null,
      max: 100,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.getEnvelope();
    this.getEnvelopeFeedback();
  },

  methods: {
    getEnvelope() {
      fetchEnvelope(this.$route.params.envelope_id)
        .then((response) => {
          // JSON responses are automatically parsed.
          this.envelope = response.data;
          this.envelopeState = envelopeCodeDictionary(response.data.workflow.available_transitions[0]);

          for (let index = 0; index < this.envelope.files.length; index += 1) {
            this.envelope.files[index] = Object.assign({}, this.envelope.files[index], { availableScripts: [] });
          }
        })
        .catch((e) => {
          console.log(e);
        });
    },

    getEnvelopeFeedback() {
      fetchEnvelopeFeedback(this.$route.params.envelope_id)
        .then((response) => {
          this.envelopeFeedback = response.data;
        });
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
      const funcs = this.files.map((file, index) => () => this.uploadFile(file, index));

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

    goToTransition(e, transition) {
      e.preventDefault();

      runEnvelopeTransition(this.$route.params.envelope_id, transition)
        .then((response) => {
          this.getEnvelope(this.$route.params.envelope_id);
        })
        .catch((error) => {
          console.log(error);
        });
    },

    translateCode(code) {
      return envelopeCodeDictionary(code);
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.sidebar-item {
  border-top: 1px solid rgba(0,0,0,.15);
  margin-top: 1rem;
  padding-top: 1rem;
}
</style>
