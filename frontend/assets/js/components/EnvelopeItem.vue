<template>
  <div class="hello">
    <div v-if="envelope">

      <b-card title="Details">
        <p><strong>name: {{envelope.name}}</strong></p>
        <p>country: {{envelope.country}}</p>
        <p>reporting_period: {{envelope.reporting_period.start}}</p>
        <p>reporting_period: {{envelope.created_at.end}}</p>
        <p>current_state {{envelope.current_state}}</p>
        <p>created_at {{envelope.created_at}}</p>
        <b-link href="#" class="card-link">Edit Envelope</b-link>
      </b-card>

      <b-card title="History">
        <p>{{envelopeHistory}}</p>
      </b-card>

      <p><strong>Envelope files {{envelope.files.length}}</strong></p>
      <b-tabs>
        <b-tab title="all" active>
          <br>All
          <b-table
            :hover="false"
            :items="envelope.files"
            :fields="fields">

            <template slot="file" scope="row">
              <a v-bind:href="row.value">Edit File</a>
            </template>

            <template slot="show_details" scope="row">
              <!-- In some circumstances you may need to use @click.native.stop instead -->
              <!-- As `row.showDetails` is one-way, we call the toggleDetails function on @change -->
              <b-form-checkbox @click.native.stop @change="row.toggleDetails" v-model="row.detailsShowing">
              </b-form-checkbox>
            </template>

          </b-table>
        </b-tab>
        <b-tab title="restricted">
          <br>Restricted from public
        </b-tab>
        <b-tab title="public">
          <br>Public
        </b-tab>
        <b-tab title="feedback">
          <br>Feedback
        </b-tab>
      </b-tabs>

      <form enctype="multipart/form-data" novalidate v-if="isInitial || isSaving">
        <h1>Upload images</h1>
        <div class="dropbox">
          <input type="file" multiple :disabled="isSaving" v-on:change="onFileChange">
            <p v-if="isInitial">
              Drag your file(s) here to begin<br> or click to browse
            </p>
            <p v-if="isSaving">
              Uploading {{ fileCount }} files...
            </p>
            <button v-on:click="uploadFile">Upload</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import tus from 'tus-js-client';
import { fetchEnvelopeItem, fetchEnvelopeToken } from '../api';

export default {
  name: 'EnvelopeItem',
  data() {
    return {
      fields: [ 'show_details', 'name', 'file' ],
      envelope: null,
      isSaving: false,
      isInitial: true,
      file: null,
      envelopeHistory: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    fetchEnvelopeItem(this.$route.params.envelope_id)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelope = response.data;
      })
      .catch((e) => {
        console.log(e);
      });
  },

  methods: {
    onFileChange(e) {
      this.file = e.target.files[0];
    },
    uploadFile(e) {
      e.preventDefault();
      fetchEnvelopeToken(this.$route.params.envelope_id)
        .then((response) => {
          const token = response.data.token;

          // Create a new tus upload
          const upload = new tus.Upload(this.file, {
            endpoint: 'http://localhost:1080/files/',
            metadata: {
              token,
              filename: this.file.name,
            },
            retryDelays: [0, 1000, 3000, 5000],
            onError: function onError(error) {
              console.log('Failed because: ', error);
            },
            onProgress: function onProgress(bytesUploaded, bytesTotal) {
              const percentage = ((bytesUploaded / bytesTotal) * 100).toFixed(2);
              console.log(bytesUploaded, bytesTotal, percentage, '%');
            },
            onSuccess: function onSuccess() {
              console.log('Download %s from %s', upload.file.name, upload.url);
            },
          });

          // Start the upload
          upload.start();
        });
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
