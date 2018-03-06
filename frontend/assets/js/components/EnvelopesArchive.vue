<template>
  <div :class="[{ 'dashboard-component': context }, 'envelope-listing']">

    <b-row class="envelope-listing-header">
      <h1>Envelopes archive</h1>
      <router-link
        class="btn btn-primary"
        v-if="!context"
        :to="'/dashboard'"
      >
      Dashboard
      </router-link>
    </b-row>
      <b-row
        class="envelope-listing-item"
        v-for="envelope in envelopes"
        :key="envelope.id"
      >
        <div class="status-badge">
          <b-badge pill :variant="envelopeCodeDictionaryVariants(envelope.workflow.current_state)">
            {{envelope.workflow.current_state.charAt(0).toUpperCase()}}
          </b-badge>
        </div>
        <div class="envelope-name-wrapper">
          <div class="envelope-name">
              <router-link
                class="router-link"
                :to="{name:'EnvelopeDetail', params: {envelopeId: `${envelope.id}`}}"
              >
              {{envelope.name}}
              </router-link>
          </div>
          <div class="mb-1 mt-1">
            <strong>Obligation:</strong>
            <b-btn
              variant="link"
              style="padding: 0;"
              v-on:click="goToObligation(envelope.obligation.id)"
            >
              {{envelope.obligation.title}}
            </b-btn>
          </div>
          <div>
            <strong>Status:</strong> <span class="muted">{{translateCode(envelope.workflow.current_state)}}</span>
          </div>
           <div>
            <strong>Last transition:</strong> <span class="muted">{{fromatDate(envelope.workflow.updated_at, 2)}}</span>
          </div>
        </div>
        <div class="envelope-reporting-period">
          <div>
            <strong>Reporting period</strong>
          </div>
          <div class="reporting-period muted">
            {{fromatDate(envelope.reporting_cycle.reporting_start_date, 2)}} - {{fromatDate(envelope.reporting_cycle.reporting_end_date, 2)}}
          </div>
        </div>
      </b-row>
    <p v-if="!envelopes || envelopes.length == 0"> No envelopes finalized yet</p>
  </div>
</template>

<script>
import { fetchArchiveEnvelopes } from '../api';
import utilsMixin from '../mixins/utils';
import {dateFormat} from '../utils/UtilityFunctions';

export default {
  name: 'EnvelopesArchive',

  data() {
    return {
      envelopes: [],
    };
  },

  mixins: [utilsMixin],


  props: {
    context: null,
    archiveCount: null,

  },

  created() {
    fetchArchiveEnvelopes(this.$route.params.reporterId)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelopes = this.context ? response.data.slice(0,this.archiveCount) : response.data;
        this.$emit('archiveLoaded', response.data.length)
      })
      .catch((e) => {
        console.log(e);
      });
  },

  methods: {
    fromatDate(date, count){
      return dateFormat(date, count)
    },

    goToObligation(id){
      this.$router.push({ name: 'ObligationDetail', params: { obligationId: id } });
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss">

</style>
