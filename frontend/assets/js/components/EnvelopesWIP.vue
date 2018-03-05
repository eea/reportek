<template>
  <div>
    <div class="envelope-list" v-if="envelopes && envelopes.length">
    <h1>Envelopes and subcollections</h1>
    <router-link
      class="btn btn-primary"
      :to="'/dashboard'"
    >
    Create New Envelope
    </router-link>
    <!--   <b-table
        :hover="false"
        :items="envelopes"
        :fields="fields"
      >
        <router-link
          slot="name"
          slot-scope="envelope"
          class="nav-link"
          :to="`/envelopes/${envelope.item.id}`"
        >
          {{envelope.value}}
        </router-link>
      </b-table> -->

      <b-row class="envelope-list-item" v-for="envelope in envelopes">
        <b-col lg="1">
          <b-badge pill :variant="envelopeCodeDictionaryVariants(envelope.workflow.current_state)">
            {{envelope.workflow.current_state.charAt(0).toUpperCase()}}
          </b-badge>
        </b-col>
        <b-col lg="8">
          <div class="envelope-name">
              <router-link
                class="router-link"
                :to="`/envelopes/${envelope.id}`"
              >
              {{envelope.name}}
              </router-link>
          </div>
          <div>
            <strong>Obligation:</strong> None
          </div>
          <div>
            <strong>Status:</strong> {{translateCode(envelope.workflow.current_state)}}
          </div>
        </b-col>
        <b-col lg="3">
          <div>
            <strong>Reporting period</strong>
          </div>
          {{envelope.reporting_cycle.reporting_start_date}} - {{envelope.reporting_cycle.reporting_end_date}} 2018-02-01
        </b-col>
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
      fields: ['name', 'files_count', 'created_at', 'finalized', 'reporting_period_start', 'reporting_period_end'],
      envelopes: [],
    };
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
    border-top: 1px solid #ddd;
    margin-top:1rem;
    margin-bottom: 1rem;
    padding-top:.5rem;
    padding-bottom: .5rem;
    &:last-of-type {
      border-bottom: 1px solid #ddd;
    }
  }
  .envelope-name {
    .router-link {
      font-size: 1.7rem;
    }
  }
  .col-lg-1 {
    max-width: 3%;
    display: flex;
    padding-top: .5rem;
    justify-content:center;
  }
  .badge-pill {
    line-height: 1.4;
    height: 22px;
  }
  h1 {
    font-weight: 400;
  }
}
</style>
