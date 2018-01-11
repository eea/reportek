<template>
  <div class="hello">
    <p> Envelope item</p>
    <div v-if="envelope">
      <p><strong>name: {{envelope.name}}</strong></p>
      <p>country: {{envelope.country}}</p>
      <p>reporting_period: {{envelope.reporting_period.start}}</p>
      <p>reporting_period: {{envelope.created_at.end}}</p>
      <p>current_state {{envelope.current_state}}</p>
      <p>created_at {{envelope.created_at}}</p>
      <p>Files: </p>
      <ul v-if="envelope.files && envelope.files.length">
        <li v-for="file of envelope.files" :key="file.id">
          <a v-bind:href="file.url">{{file.name}}</a>
        </li>
      </ul>

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
      envelope: null,
      isSaving: false,
      isInitial: true,
      file: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    fetchEnvelopeItem(this.$route.params.envelope_id)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelope = response.data;
      });
      // .catch((e) => {
      //   // consol-e.log(e);
      // });
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
