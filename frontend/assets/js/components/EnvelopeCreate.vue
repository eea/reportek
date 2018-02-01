<template>
  <div>
    <b-form @submit="onSubmit" @reset="onReset">

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
        id="obligationSpecsGroup"
        label="Obligation Spec:"
        label-for="obligationSpecsInput"
      >
        <b-form-select
          id="obligationSpecsInput"
          :options="obligationSpecs"
          required
          v-model="form.obligationSpec"
        >

        </b-form-select>
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
import { fetchReporters,
        fetchObligationSpecs,
        fetchReportingCycles,
        createEnvelope,
      } from '../api';

export default {
  data() {
    return {
      form: {
        name: '',
        reporter: 10,
        obligationSpec: null,
        reportingCycle: null,
      },
      obligationSpecs: [],
      reportingCycles: [],
    };
  },

  // Fetches posts when the component is created.
  created() {
    if(!this.$route.params.reportingCycle && !this.$route.params.spec) {
      this.$router.push({ name: 'Dashboard' });
    }
    this.getApiData();
  },

  methods: {
    onSubmit(evt) {
      evt.preventDefault();
      createEnvelope(this.form)
        .then((response) => { this.$router.push({
            name: 'EnvelopeDetail',
            params: {
              id: 1,
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
      this.form.obligationSpec = null;
      this.form.reportingCycle = null;
      this.$router.push({ name: 'Dashboard' });
    },

    getApiData() {
      this.obligationSpecs = [
        {
          value: this.$route.params.spec.id,
          text: this.$route.params.spec.id,
        }];
      this.reportingCycles = [
        {
          value: this.$route.params.reportingCycle.id,
          text: this.$route.params.reportingCycle.reporting_start_date,
        }];
      this.form.obligationSpec = this.$route.params.spec.id;
      this.form.reportingCycle =this.$route.params.reportingCycle.id;
      // fetchObligationSpecs();
      // fetchReportingCycles();
    },
  },
};
</script>

<style>

</style>
