<template>
  <div>
    Dashboard

    <wip></wip>
    <obligations-pending></obligations-pending>

    <router-link
      class="nav-link"
      :to="`/archive/`"
    >
      archive
    </router-link>

    <router-link
      class="nav-link"
      :to="`/envelopes/`"
    >
      envelopes
    </router-link>

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
      fields: [],
    };
  },

  // Fetches posts when the component is created.
  created() {

  },

  methods: {
  },
}
</script>

<style>

</style>
