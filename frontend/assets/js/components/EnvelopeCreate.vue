<template>
  <div class="create-envelope clearfix">
    <div class="breadcrumbs">
        <router-link
           :to="{name:'Dashboard', params: {reporterId: `${$route.params.reporterId}`}}"
          >
          Dashboard
        </router-link>
        <span class="separator">/</span>
        <router-link
           :to="{name:'ObligationsPending', params: {reporterId: `${$route.params.reporterId}`}}"
          >
          Pending obligations
        </router-link>
        <span class="separator">/</span>
        <span class="current-page">Create envelope</span>
      </div>
    <h1>New envelope</h1>
    <p class="muted" style="font-size: .8rem">Fill out the fields in this report profile and click Add. This will create an envelope into which you make the delivery</p>
    <b-form
      v-on:submit="onSubmit"
      v-on:reset="onReset"
    >

      <b-form-group
        id="envelopeName"
        label="Title:"
        label-for="envelopeNameInput"
      >
        <b-form-input
          id="envelopeNameInput"
          type="text"
          v-model="form.name"
          required
          placeholder="Enter name"
        >
        </b-form-input>
      </b-form-group>

      <b-form-group
        id="descriptionGroup"
        label="Description:"
        label-for="descriptionInput"
      >
        <b-form-textarea
          id="descriptionInput"
          v-model="form.description"
          placeholder="Enter Description"
          :rows="3"
        >
        </b-form-textarea>
      </b-form-group>

      <b-form-group
        id="reportingCyclesGroup"
        label="Reporting Cycle:"
        label-for="reportingCyclesInput"
      >
        <b-form-select
          id="reportingCyclesInput"
          :options="reportingCycles"
          required
          style="max-width: 300px!important;"
          v-model="form.reportingCycle"
        >
        </b-form-select>
      </b-form-group>


      <div class="mb-2">
        <label>Coverage:</label><span class="muted"> {{form.country}}</span>
      </div>

      <b-form-group
        id="coverage_noteGroup"
        label="Coverage notes:"
        label-for="coverage_noteInput"
      >
        <b-form-input
          type="text"
          id="coverage_noteInput"
          v-model="form.coverage_note"
          placeholder="Enter coverage notes"
          :rows="1"
        >
        </b-form-input>
      </b-form-group>

      <div class="button-group">
        <b-button
          type="submit"
          variant="primary"
        >Add
        </b-button>
        <button class='btn btn-transparent'
          type="reset"
        >Cancel</button>
      </div>
    </b-form>
  </div>
</template>

<script>
import { createEnvelope, fetchUserProfile } from '../api';

export default {
  data() {
    return {
      form: {
        name: '',
        reporter: null,
        obligationSpec: null,
        reportingCycle: null,
        country: null,
        description: '',
        coverage_note: '',
      },
      reportingCycles: [],
    };
  },

  // Fetches posts when the component is created.
  created() {
          console.log('this.$route.params ', this.$route.params)
    if (!this.$route.params.reportingCycle) {
      this.$router.push({ name: 'Dashboard' });
    }
    fetchUserProfile().then((response) => {
      this.getApiData(response.data);
    })
  },

  methods: {
    onSubmit(evt) {
      evt.preventDefault();
      createEnvelope(this.form)
        .then((response) => {
          this.$router.push({
            name: 'EnvelopeDetail',
            params: {
              envelopeId: response.data.id,
            },
          });
        })
        .catch((e) => {
          console.log(e);
        });
    },

    onReset(evt) {
      evt.preventDefault();
      /* Reset our form values */
      this.form.reporter = null;
      this.form.name = null;
      this.form.reportingCycle = null;
      this.$router.push({ name: 'Dashboard', params: { reporterId: this.$route.params.reporterId } });
    },

    getApiData(userProfile) {
      this.reportingCycles = [
        {
          value: this.$route.params.reportingCycle.id,
          text: this.$route.params.reportingCycle.reporting_start_date,
        }];
      this.form.country = userProfile.reporters[0].name
      this.form.reportingCycle = this.$route.params.reportingCycle.id;
      this.form.reporter = this.$route.params.reporterId;
      this.form.obligationSpec = this.$route.params.reportingCycle.obligation_spec.id;
    },
  },
};
</script>

<style lang="scss">
  .create-envelope {
    max-width: 915px;
    margin: auto;
    h1 {
      margin-top: 2rem;
      border-bottom: 1px solid #eee;
      padding-bottom: .5rem;
      font-weight: 400;
    }
    label {
      font-weight: bold;
    }
    .button-group {
      float: right;
    }
    textarea {
      max-width: 760px;
    }
  }
</style>
