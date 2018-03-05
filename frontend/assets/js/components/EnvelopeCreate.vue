<template>
  <div>
    <b-form
      v-on:submit="onSubmit"
      v-on:reset="onReset"
    >

      <b-form-group
        id="envelopeName"
        label="Envelope Name:"
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
        id="reportingCyclesGroup"
        label="Reporting Cycle:"
        label-for="reportingCyclesInput"
      >
        <b-form-select
          id="reportingCyclesInput"
          :options="reportingCycles"
          required
          v-model="form.reportingCycle"
        >
        </b-form-select>
      </b-form-group>

      <b-button
        type="submit"
        variant="primary"
      >Submit
      </b-button>
      <b-button
        type="reset"
        variant="danger"
      >Cancel</b-button>
    </b-form>
  </div>
</template>

<script>
import { createEnvelope } from '../api';

export default {
  data() {
    return {
      form: {
        name: '',
        reporter: null,
        obligationSpec: null,
        reportingCycle: null,
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
    this.getApiData();
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

    getApiData() {
      this.reportingCycles = [
        {
          value: this.$route.params.reportingCycle.id,
          text: this.$route.params.reportingCycle.reporting_start_date,
        }];
      this.form.reportingCycle = this.$route.params.reportingCycle.id;
      this.form.reporter = this.$route.params.reporterId;
      this.form.obligationSpec = this.$route.params.reportingCycle.obligation_spec.id;
    },
  },
};
</script>

<style>

</style>
