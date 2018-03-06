<template>
  <div class="create-envelope clearfix">
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

      <div class="button-group">
        <b-button
          type="submit"
          variant="primary"
        >Submit
        </b-button>
        <button class='btn btn-transparent'
          type="reset"
        >Cancel</button>
      </div>
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

<style lang="scss">
  .create-envelope {
    max-width: 500px;
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
  }
</style>
