<template>
  <div class="hello">
    Obligations Pending
    <b-container class="bv-example-row">
        <b-row v-if="obligationsPending">
          <b-col cols="8">
            {{obligationsPending.title}}
          </b-col>
          <b-col cols="4">
            <b-row
              v-for="spec in obligationsPending.specs"
              :key="spec.id"
            >
            <span
              v-for="reportingCycle in spec.reporting_cycles"
              :key="reportingCycle.id"
            >
              {{reportingCycle.reporting_start_date}}

              <router-link
                :to="{ name: 'EnvelopeCreate', params: { reportingCycle: reportingCycle, spec: spec } }"
                class="btn btn-primary"
              >
                Create New Envelop for this cycle
              </router-link>
            </span>
            </b-row>
          </b-col>
        </b-row>
    </b-container>
  </div>
</template>

<script>
import { fetchObligationsPending } from '../api';

export default {
  name: 'EnvelopesWIP',

  data() {
    return {
      obligationsPending: null,
    };
  },

  created() {
    fetchObligationsPending()
      .then((response) => {
        // JSON responses are automatically parsed.
        this.obligationsPending = response.data;
      })
      .catch((e) => {
        console.log(e);
      });
  },
};
</script>

<style>

</style>
