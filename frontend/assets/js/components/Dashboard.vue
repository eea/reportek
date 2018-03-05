<template>
  <div>

    <div>
      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesWIP'}"
      >
        WIP
      </router-link>

      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesArchive', params: { spec: 1 } }"
      >
        Archive
      </router-link>
      
      <obligations-pending ></obligations-pending>
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
    };
  },

  methods: {
  },
};
</script>

<style>

</style>
