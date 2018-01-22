<template>
  <div class="hello">
    <div v-if="envelope">

      <b-card title="Details">
        <p><strong>name: {{envelope.name}}</strong></p>
        <p>country: {{envelope.country}}</p>
        <p>reporting_period: {{envelope.reporting_cycle}}</p>
        <p>reporting_period: {{envelope.created_at.end}}</p>
        <p>current_state {{envelope.current_state}}</p>
        <p>created_at {{envelope.created_at}}</p>
        <b-link href="#" class="card-link">Edit Envelope</b-link>
      </b-card>

      <b-card title="History">
        <p>{{envelopeHistory}}</p>
      </b-card>

      <p><strong>Envelope files {{envelope.files.length}}</strong></p>

      <b-button
        variant="success"
        v-on:click="uploadAllFiles">
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
                v-on:click="getFileScripts(row.item.id)"
              >
                Run Tests
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
              :key="file.file.name"
            >
              {{file.file.name}}

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
  </div>
</template>

<script>
import tus from 'tus-js-client';
import { fetchEnvelope,
          fetchEnvelopeToken,
          fetchEnvelopeHistory,
          fetchEnvelopeFeedback,
          fetchEnvelopeFilesQAScripts,
          runEnvelopeFilesQAScript,
          fetchEnvelopeFiles
          } from '../api';

export default {
  name: 'EnvelopeItem',
  data() {
    return {
      fields: [ 'select', 'name', 'file', 'tests' ],
      envelope: null,
      isSaving: false,
      isInitial: true,
      files: [],
      envelopeHistory: null,
      envelopeFeedback: null,
      max: 100,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.getEnvelope();
    this.getEnvelopeFeedback();
    this.getEnvelopeHistory();
  },

  methods: {
    onFileChange(e) {
      const newfiles = e.target.files;

      for (const file of newfiles) {
        this.files.push({file: file, percentage: 0});
      }
    },

    uploadAllFiles(e) {
      e.preventDefault();

      // for each file create a function that returns a promise
      const funcs = this.files.map((file, index) => () => this.uploadFile(file, index))

      // reduce the array or functions that return promises, in a chain
      const promiseSerial = funcs =>
        funcs.reduce((promise, func) =>
          promise.then(result =>
            func().then(result => {this.updateFilesList();})
          ),
          Promise.resolve([])
        );

      // execute Promises in serial, clear files at the end of all promisees
      promiseSerial(funcs)
        .then(() => {this.files = [];})
        .catch(console.error.bind(console));
    },

    uploadFile(file, index) {
      // Create a new tus upload
      var self = this;
      return new Promise((resolve, reject) => {

        fetchEnvelopeToken(this.$route.params.envelope_id)
          .then((response) => {
            const token = response.data.token;

            const upload = new tus.Upload(file.file,
              {
                endpoint: 'http://localhost:1080/files/',
                metadata: {
                  token,
                  filename: file.file.name,
                  index: index,
                  fileId: file.file.id
                },
                retryDelays: [0, 1000, 3000, 5000],
                onError: function onError(error) {
                  console.log('Failed because: ', error);
                  reject(error);
                },
                onProgress: function onProgress(bytesUploaded, bytesTotal) {
                  const index = this.metadata.index;
                  const percentage = file.percentage = parseInt(((bytesUploaded / bytesTotal) * 100).toFixed(2));
                  console.log(bytesUploaded, bytesTotal, percentage, '%');
                },
                onSuccess: function onSuccess() {
                  console.log('Download %s from %s', upload.file.name, upload.url);
                  resolve(
                    {
                      fileName: upload.file.name,
                      uploadUrl: upload.url
                    }
                  );
                },
              });
              // Start the upload
              upload.start();
            });
      });
    },

    getEnvelope() {
      fetchEnvelope(this.$route.params.envelope_id)
        .then((response) => {
          // JSON responses are automatically parsed.
          this.envelope = response.data;
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

    getEnvelopeHistory() {
      fetchEnvelopeHistory(this.$route.params.envelope_id)
        .then((response) => {
          this.envelopeHistory = response.data;
        });
    },

    getFileScripts(fileId) {
      console.log('file scrips!!');
      const self = this;
      fetchEnvelopeFilesQAScripts(this.$route.params.envelope_id, fileId)
        .then(function (response) {
          console.log(response);
          const script_id = response.data[0].id;
          runEnvelopeFilesQAScript(self.$route.params.envelope_id, fileId, script_id)
            .then(function (response) {
              console.log('runEnvelopeFilesQAScript ', response);
            })
            .catch(function (error) {
              console.log(error);
            });
        })
        .catch(function (error) {
          console.log(error);
        });

    },

    updateFilesList() {
      return this.pollFiles(() => fetchEnvelopeFiles(this.$route.params.envelope_id), 500);
    },

    pollFiles(fn, delay) {
      const self = this;
      let pollFiles = setTimeout(() => {
        fn()
          .then(function (response) {
            if(self.envelope.files.length === response.data.length) {
              self.pollFiles(fn, delay);
            } else {
              for (let index = 0; index <= response.data.length; index++) {
                const responseFile = response.data[index];
                const found = self.envelope.files.find(function(file) {
                  return file.id === responseFile.id;
                });

                if(found === undefined) {
                  self.envelope.files.push(response.data[index]);
                  self.files.shift();
                }
              }
            }
          })
          .catch(function (error) {
            console.log(error);
          });
      }, delay);
    }
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
