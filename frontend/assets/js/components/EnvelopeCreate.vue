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
        id="reportersGroup"
        label="Reporter:"
        label-for="reporterInput"
      >
        <b-form-select
          id="reporterInput"
          :options="reporters"
          required
          v-model="form.reporter"
        >
        </b-form-select>
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

      <b-button type="submit" variant="primary">Submit</b-button>
      <b-button type="reset" variant="danger">Cancel</b-button>
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
        reporter: null,
        obligationSpec: null,
        reportingCycle: null,
      },
      reporters: [],
      obligationSpecs: [],
      reportingCycles: [],
    };
  },


  // Fetches posts when the component is created.
  created() {
    this.getApiData();
  },

  methods: {
    onSubmit(evt) {
      evt.preventDefault();
      alert(JSON.stringify(this.form));
    },

    onReset(evt) {
      evt.preventDefault();
      /* Reset our form values */
      this.form.reporter = null;
      this.form.name = null;
      this.form.obligationSpec = null;
      this.form.reportingCycle = null;
      this.$router.push({ name: 'Envelopes' });
    },

    getApiData() {
      fetchReporters();
      fetchObligationSpecs();
      fetchReportingCycles();
    },
  },
};
</script>

<style>

</style>
