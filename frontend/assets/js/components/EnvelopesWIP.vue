<template>
  <div>
    <div class="envelope-list" v-if="envelopes && envelopes.length">

    <b-row class="envelope-list-header">
      <h1>Envelopes in progress</h1>
      <router-link
        class="btn btn-primary"
        :to="'/dashboard'"
      >
      Dashboard
      </router-link>
    </b-row>
      <b-row
        class="envelope-list-item"
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
                :to="`${envelope.id}`"
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
    </div>

    <p v-if="!envelopes || envelopes.length == 0"> No envelopes created yet</p>
  </div>
</template>

<script>
import { fetchWipEnvelopes } from '../api';
import utilsMixin from '../mixins/utils';
import {dateFormat} from '../utils/UtilityFunctions';

export default {
  name: 'Envelopes',

  mixins: [utilsMixin],

  data() {
    return {
      fields: ['name', 'files_count', 'created_at', 'finalized', 'reporting_period_start', 'reporting_period_end'],
      envelopes: [],
    };
  },

  methods: {
    fromatDate(date, count){
      return dateFormat(date, count)
    },

    goToObligation(id){
      this.$router.push({ name: 'ObligationDetail', params: { obligationId: id } });
    },
  },

  created() {
    fetchWipEnvelopes(this.$route.params.reporterId)
      .then((response) => {
        // JSON responses are automatically parsed.
        this.envelopes = response.data;
      })
      .catch((e) => {
        console.log(e);
      });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss">
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}

a.btn-primary {
  color: #fff;
}

.envelope-list {
  .envelope-list-item {
    border-top: 1px solid #eee;
    margin-top:1rem;
    margin-bottom: 1rem;
    padding-top:.5rem;
    padding-bottom: .5rem;
    &:last-of-type {
      border-bottom: 1px solid #eee;
    }
  }
  .envelope-name {
    .router-link {
      font-size: 1.5rem;
      font-weight: bold;
    }
  }
  .status-badge {
    display: flex;
    padding-top: .5rem;
    margin-right: 1rem;
    justify-content:center;
  }
  .envelope-reporting-period {
    justify-content: center;
    display: flex;
    flex-direction: column;
  }
  .envelope-name-wrapper {
    flex-grow: 1;
  }
  .badge-pill {
    line-height: 1.4;
    height: 22px;
  }
  h1 {
    font-weight: 400;
    flex-grow: 1;
  }
  .envelope-list-header {
    margin-top: 2rem;
    display: flex;
    align-items: center;
  }
  .reporting-period {
    font-size: .9rem;
  }
}
</style>
