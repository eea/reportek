<template>
  <div>
    <div class="dashboard">
      <b-row class="dashboard-title">
        <h1>Envelopes</h1>
      </b-row>


      <wip
        v-on:envelopesWipLoaded="handleEnvelopesWipLoaded($event)"
        context="dashboardComponent"
        :envelopesCount="envelopesCount"
      >
      </wip>
      <div v-if="showMoreWip" class="show-more">
        <span>Showing {{envelopesCount}} out of {{actualLength.envelopesWipLength}} envelopes.</span>
        <router-link
          class="nav-link"
          style="display: inline-block"
          :to="{ name: 'EnvelopesWIP'}"
        >
        Show more
        </router-link>
      </div>


      <envelopeArchive
        v-on:archiveLoaded="handleArchiveLoaded($event)"
        :archiveCount="archiveCount"
        context="dashboardComponent"
      >
      </envelopeArchive>
      <div v-if="showMoreArchive" class="show-more">
        <span >Showing {{archiveCount}} out of {{actualLength.archiveLength}} envelopes.</span>
        <router-link
          class="nav-link"
          style="display: inline-block"
          :to="{ name: 'EnvelopesArchive', params: { spec: 1 } }"
        >
          Show more
        </router-link>
      </div>


      <obligations-pending
        context="dashboardComponent"
        v-on:obligationsLoaded="handleObligationsLoaded($event)"
        :obligationsCount="obligationsCount"
      >
      </obligations-pending>

      <div v-if="showMoreObligations" class="show-more">
        <span v-if="showMoreObligations">Showing {{obligationsCount}} out of {{actualLength.obligationsLength}} obligations.</span>
        <router-link
          class="nav-link"
          style="display: inline-block"
          :to="{ name: 'ObligationsPending', params: { reporterId: `${$route.params.reporterId}` } }"
        >
          Show more
        </router-link>
      </div>


    </div>

  </div>
</template>

<script>
import WIP from './EnvelopesWIP';
import EnvelopeArchive from './EnvelopesArchive';
import ObligationsPending from './ObligationsPending';

export default {
  name: 'Dashboard',

  components: {
    wip: WIP,
    envelopeArchive: EnvelopeArchive,
    obligationsPending: ObligationsPending,
  },

  data() {
    return {
      obligationsCount: 1,
      envelopesCount: 1,
      archiveCount: 2,
      showMoreWip: false,
      showMoreObligations: false,
      showMoreArchive: false,
      actualLength: {
        envelopesWipLength: null,
        archiveLength: null,
        obligationsLength: null,
      },
    };
  },

  methods: {
    handleEnvelopesWipLoaded(count){
      this.actualLength.envelopesWipLength = count;
      this.showMoreWip = count > this.envelopesCount;
    },

    handleArchiveLoaded(count){
      console.log('a intrat aici', count)
      this.actualLength.archiveLength = count;
      this.showMoreArchive = count > this.archiveCount;
    },

    handleObligationsLoaded(count){
      this.actualLength.obligationsLength = count;
      this.showMoreObligations = count > this.obligationsCount;
    }
  },
};
</script>

<style lang="scss">
.dashboard-component {
  h1 {
    font-size: 1.4rem;
  }

  .envelope-listing-header {
    margin-top: 1rem!important;
  }

  .badge-pill {
    line-height: 1.4;
    height: 41px!important;
    font-size: 1.3rem;
  }
  .envelope-name .router-link{
    font-size: 1.4rem!important;
    font-weight: 400!important;
  }
   .obligation-name {
    .router-link {
      font-weight: 400!important;
    }
  }
  .obligations-pending-item {
    padding-left: 53px;
  }
  .reporting-period {
      min-width: 16rem;
  }


}

.dashboard {
  .nav-link {
    padding: 0;
  }

 .dashboard-title {
  margin-top: 2rem;
  border-bottom: 1px solid #eee;
 }

  .show-more {
    display: block;
    background: #f7f7f7;
    padding: .5rem;
    font-size: .8rem;
    margin-top: -1rem;
    margin-left: .5rem;
    margin-right: .5rem;
    padding-left: 2rem;
  }
}
</style>
