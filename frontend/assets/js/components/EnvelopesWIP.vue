<template>
  <div>
    <div :class="[{ 'dashboard-component': context }, 'envelope-listing']" v-if="envelopes && envelopes.length">
    <div v-if="!context" class="breadcrumbs">
      <router-link
         :to="{name:'Dashboard', params: {reporterId: `${$route.params.reporterId}`}}"
        >
        Dashboard
      </router-link>
      <span class="separator">/</span>
      <span class="current-page">Envelopes in progress</span>
    </div>
    <b-row class="envelope-listing-header">
      <h1 v-if="!context">Envelopes in progress</h1>
      <h4 v-else>Work in progress</h4>
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
            <strong>Last transition:</strong> <span class="muted">{{formatDate(envelope.workflow.updated_at, 2)}}</span>
          </div>
        </div>
        <div class="envelope-reporting-period">
          <div>
            <strong>Reporting period</strong>
          </div>
          <div class="reporting-period muted">
            {{formatDate(envelope.reporting_cycle.reporting_start_date, 2)}} - {{formatDate(envelope.reporting_cycle.reporting_end_date, 2)}}
          </div>
        </div>
      </b-row>
    </div>

    <p v-if="!envelopes || envelopes.length == 0"> No envelopes created yet</p>
  </div>
</template>

<script>
import { fetchWipEnvelopes } from '../api';
import utilsMixin from '../mixins/utils';

export default {
  name: 'Envelopes',

  mixins: [utilsMixin],

  data() {
    return {
      envelopes: [],
    };
  },

  props: {
    context: null,
    envelopesCount: null,
  },

  methods: {

    goToObligation(id) {
      this.$router.push({ name: 'ObligationDetail', params: { obligationId: id } });
    },

    getWipEnvelopes() {
      fetchWipEnvelopes(this.$route.params.reporterId)
        .then((response) => {
          this.envelopes = this.context ? response.data.slice(0, this.envelopesCount) : response.data;
          this.$emit('envelopesWipLoaded', response.data.length);
        })
        .catch((e) => {
          console.log(e);
        });
    },
  },

  created() {
    this.getWipEnvelopes();
  },

  watch: {
    $route(to, from) {
      if (from && (to.params.reporterId != from.params.reporterId)) {
        this.getWipEnvelopes();
      }
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss">
</style>
