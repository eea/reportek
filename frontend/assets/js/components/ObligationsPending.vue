<template>
  <div :class="[{ 'dashboard-component': context }, 'obligations-pending']">
    <b-row v-if="obligationsPending" class="obligations-pending-header">
      <h1 v-if="!context">Pending obligations</h1>
      <h1 v-else>Pending obligations</h1>
    </b-row>
      <b-row
        class="obligations-pending-item"
        v-for="obligation in obligationsPending"
        :key="obligation.id"
      >
        <div class="obligations-name-wrapper">
          <div class="obligation-name">
              <router-link
                class="router-link"
                :to="{ name:'ObligationDetail', params: { obligationId: `${obligation.id}` }}"
              >
              {{obligation.title}}
              </router-link>
          </div>
          <div class="mb-1 mt-1">
            <strong>Instrument:</strong>
            <b-btn
              variant="link"
              style="padding: 0;"
            >
              {{obligation.instrument}}
            </b-btn>
          </div>
        </div>
        <div class="obligations-reporting-period">
          <div>
            <strong>Reporting period</strong>
          </div>
          <div
            v-for="cycle in obligation.reporting_cycles"
            :key="cycle.id"
            class="reporting-period"
          >
            <span class="muted">
              {{formatDate(cycle.reporting_start_date, 2)}} - {{formatDate(cycle.reporting_end_date,2)}}
            </span>
            <router-link
              :to="{ name: 'EnvelopeCreate', params: { reportingCycle: cycle } }"
              class="btn btn-primary create-envelope"
            >
               New Envelope
            </router-link>
          </div>
        </div>

      </b-row>
  </div>
</template>

<script>
import { fetchObligationsPending } from '../api';
import utilsMixin from '../mixins/utils';
import {dateFormat} from '../utils/UtilityFunctions';

export default {
  name: 'obligationsWIP',

  data() {
    return {
      obligationsPending: null,
    };
  },

  props: {
    context: null,
    obligationsCount: null,
  },

  created() {
    this.getObligationsPending();
  },

  methods: {
    getObligationsPending() {
      fetchObligationsPending(this.$route.params.reporterId)
        .then((response) => {
          // JSON responses are automatically parsed.
          this.obligationsPending = this.context ? response.data.slice(0,this.obligationsCount) : response.data;
          this.$emit('obligationsLoaded', response.data.length)
        })
        .catch((e) => {
          console.log(e);
        });
    },

    formatDate(date, count){
      return dateFormat(date, count)
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

    $route(to, from) {
      if (from && (to.params.reporterId != from.params.reporterId)) {
        this.getObligationsPending();
      }
    },
  },
};
</script>

<style lang="scss">

.obligations-pending {
  .obligations-pending-header {
      margin-top: 2rem;
    display: flex;
    align-items: center;
  }
  .obligations-pending-item {
    border-top: 1px solid #eee;
    margin-top:1rem;
    margin-bottom: 1rem;
    padding-top:.5rem;
    padding-bottom: .5rem;
    &:last-of-type {
      border-bottom: 1px solid #eee;
    }
    .muted {
      transition: all 200ms;
    }
    &:hover {
      .create-envelope {
        opacity: 1;
        z-index: 1;
      }
      .muted {
        opacity: 0;
      }
    }
  }
  .obligation-name {
    .router-link {
      font-size: 1.1rem;
      font-weight: bold;
    }
  }
  .status-badge {
    display: flex;
    padding-top: .5rem;
    margin-right: 1rem;
    justify-content:center;
  }
  .obligations-reporting-period {
    justify-content: center;
    display: flex;
    flex-direction: column;
      .reporting-period {
      font-size: .9rem;
      position: relative;
      padding-bottom:1rem;
    }
  }
  .obligations-name-wrapper {
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


  .create-envelope {
    position: absolute;
    right:0;
    opacity:0;
    z-index: -1;
    transition: all 200ms;
  }
}
</style>
