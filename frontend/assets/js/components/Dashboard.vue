<template>
  <div>

    <router-link
      class="nav-link"
      :to="`/envelopes/wip`"
    >
      WIP
    </router-link>
    <router-link
      class="nav-link"
      :to="`/envelopes/archive/`"
    >
      Archive
    </router-link>

    <obligations-pending></obligations-pending>
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
