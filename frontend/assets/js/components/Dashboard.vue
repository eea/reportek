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
        Show {{actualLength.envelopesWipLength}} more
      </router-link>
      <envelopeArchive

        context="dashboardComponent"
      >
      </envelopeArchive>
      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesArchive', params: { spec: 1 } }"
      >
        Archive
      </router-link>
      <obligations-pending context="dashboardComponent" :obligationsCount="obligationsCount"></obligations-pending>
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
      obligationsCount: 3,
      envelopesCount: 3,
      archivesCount: 3,
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
      this.actualLength.archiveLength = count;
      this.showMoreArchive = count > this.archivesCount;
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
