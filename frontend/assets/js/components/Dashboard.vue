<template>
  <div>
    <div>
      <wip
        v-on:envelopesWipLoaded="handleEnvelopesWipLoaded($event)"
        context="dashboardComponent"
        :envelopesCount="envelopesCount"
      >
      </wip>
      <router-link
        class="nav-link"
        v-if="showMoreWip"
        :to="{ name: 'EnvelopesWIP'}"
      >
        Show {{actualLength.envelopesWipLength - envelopesCount}} more envelopes
      </router-link>
      <envelopeArchive
        v-on:archiveLoaded="handleArchiveLoaded($event)"
        :archiveCount="archiveCount"
        context="dashboardComponent"
      >
      </envelopeArchive>
      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesArchive', params: { spec: 1 } }"
      >
        Show {{actualLength.archiveLength - archiveCount}} more envelopes

      </router-link>
      <obligations-pending
        context="dashboardComponent"
        v-on:obligationsLoaded="handleObligationsLoaded($event)"
        :obligationsCount="obligationsCount"
      >
      </obligations-pending>
      <router-link
        class="nav-link"
        :to="{ name: 'ObligationsPending', params: { reporterId: `${$route.params.reporterId}` } }"
      >
        Show {{actualLength.obligationsLength - obligationsCount}} more obligations
      </router-link>
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

<style>

</style>
