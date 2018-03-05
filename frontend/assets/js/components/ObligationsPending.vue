<template>
  <div class="hello">
    Obligations Pending
    <b-container>
        <b-row
          v-for="obligation in obligationsPending"
          :key="obligation.id"
        >
          <b-col cols="8">
            {{obligation.title}}
          </b-col>
          <b-col cols="4">
            <b-row
              v-for="reportingCycle in obligation.reporting_cycles"
              :key="reportingCycle.id"
            >
            <span
            >
              {{reportingCycle.reporting_start_date}}

              <router-link
                :to="{ name: 'EnvelopeCreate', params: { reportingCycle: reportingCycle } }"
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
    this.getObligationsPending();
  },

  methods: {

    getObligationsPending() {
      console.log(this.$route)
      fetchObligationsPending(this.$route.params.reporterId)
        .then((response) => {
          // JSON responses are automatically parsed.
          this.obligationsPending = response.data;
          console.log('this.obligationsPending ', this.obligationsPending)
        })
        .catch((e) => {
          console.log(e);
        });
    },
  },

  watch: {
    reporterId: {
      handler(newVal, oldVal) {
        if (oldVal) {
          this.getObligationsPending();
        }
      },
    },
  },
};
</script>

<style>

</style>
