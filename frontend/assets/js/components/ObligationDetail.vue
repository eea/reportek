<template>
  <div>
    <div class="obligation-detail" v-if="obligation">
      <h1>Reporting for: {{obligation.title}}</h1>
      <h3>Details</h3>
      <b-tabs>
        <b-tab title="Overview">
          <b-row>
            <b-col lg="2">
              Description
            </b-col>
            <b-col lg="10">
              {{obligation.description}}
            </b-col>
          </b-row>
          <b-row>
            <b-col lg="2">
              Instrument
            </b-col>
            <b-col lg="10">
              {{obligation.instrument}}
            </b-col>
          </b-row>
           <b-row>
            <b-col lg="2">
              Terminated
            </b-col>
            <b-col lg="10">
              {{obligation.terminated}}
            </b-col>
          </b-row>
          <b-row>
            <b-col lg="2">
              Active period
            </b-col>
            <b-col lg="10">
              {{obligation.active_since}} - {{obligation.active_until}}
            </b-col>
          </b-row>
          <b-row>
            <b-col lg="2">
              Active period
            </b-col>
            <b-col lg="10">
              {{obligation.active_since}} - {{obligation.active_until}}
            </b-col>
          </b-row>
          <b-row>
            <b-col lg="2">
              Coverage
            </b-col>
            <b-col lg="10">
              COUNTRY
            </b-col>
          </b-row>
          <b-row>
            <b-col lg="2">
              Reported
            </b-col>
            <b-col lg="10">
              {{obligation.updated_at}}
            </b-col>
          </b-row>
        </b-tab>
        <b-tab title="Specifications">
          <div v-for="spec in obligation.specs">
            <b-row>
              <b-col lg="2">
                Url
              </b-col>
              <b-col lg="10">
                {{spec.url}}
              </b-col>
            </b-row>
            <b-row>
              <b-col lg="2">
                Draft status
              </b-col>
              <b-col lg="10">
                {{spec.draft}}
              </b-col>
            </b-row>
            <b-row>
              <b-col lg="2">
                Schema
              </b-col>
              <b-col lg="10">
                {{spec.schema[0]}}
              </b-col>
            </b-row>
            <b-row>
              <b-col lg="2">
                Reporting Cycles
              </b-col>
              <b-col lg="10">
                <div v-for="cycle in spec.reporting_cycles">
                  {{cycle.reporting_start_date}} - {{cycle.reporting_end_date}}
                </div>
              </b-col>
            </b-row>
            <b-row>
              <b-col lg="2">
                Created at
              </b-col>
              <b-col lg="10">
                {{spec.created_at}}
              </b-col>
            </b-row>
            <b-row>
              <b-col lg="2">
                Last updated
              </b-col>
              <b-col lg="10">
                {{spec.updated_at}}
              </b-col>
            </b-row>
          </div>
        </b-tab>
        <b-tab title="Legislation"></b-tab>
        <b-tab title="Deliveries"></b-tab>
        <b-tab title="Parameters"></b-tab>
        <b-tab title="History"></b-tab>
      </b-tabs>
      <br><br>
      <h2>
        Reporting dates and guidelines
      </h2>
      <b-row>
        <b-col lg="3">
          National reporting coordinators
        </b-col>
        <b-col lg="9">
          -
        </b-col>
      </b-row>
      <b-row>
        <b-col lg="3">
          National reporting contacts
        </b-col>
        <b-col lg="9">
          -
        </b-col>
      </b-row>
      <b-row>
        <b-col lg="3">
          Reporting frequency
        </b-col>
        <b-col lg="9">
          {{obligation.reporting_frequency}}
        </b-col>
      </b-row>
      <b-row>
        <b-col lg="3">
          Next report due
        </b-col>
        <b-col lg="9">
          TERMINATED
        </b-col>
      </b-row>
      <b-row>
        <b-col lg="3">
          Date comments
        </b-col>
        <b-col lg="9">
          -
        </b-col>
      </b-row>
      <b-row>
        <b-col lg="3">
          Report to
        </b-col>
        <b-col lg="9">
          <a href="#"> European Environment Agency</a>
        </b-col>
      </b-row>
    </div>
  </div>
</template>

<script>

import { fetchObligation } from '../api';

export default {

  name: 'ObligationDetail',

  data(){
    return {
      obligation: null
    }
  },

  created() {
    fetchObligation(this.$route.params.obligationId)
      .then((response) => {
        this.obligation = response.data
        console.log(response.data)
      })
      .catch((error) => {
        console.log(error)
      })
  },
}
</script>

<style lang="scss">
.obligation-detail {
  h1 {
    margin-bottom: 3rem;
    margin-top: 2rem;
  }
  h2 {
    border-bottom: 1px solid #eee;
    padding-bottom: .5rem;
  }
  .nav-item {
    margin-left: 0;
  }
  .row {
    margin-left: 0;
    margin-right: 0;
    > .col-lg-2,
    > .col-lg-3 {
      font-weight: bold;
    }
    > div {
      padding-top: .5rem;
    }
  }
}
</style>
