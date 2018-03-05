<template>
  <div>
    <b-list-group v-if="userProfile">
      <b-list-group-item
        v-for="reporter in userProfile.reporters"
        :key="reporter.id"
      >
        <router-link
          class="nav-link"
          :to="`/reporter/${reporter.id}`"
        >
          {{reporter.name}}
        </router-link>
      </b-list-group-item>
    </b-list-group>

  </div>
</template>

<script>
import WIP from './EnvelopesWIP';
import EnvelopeArchive from './EnvelopesArchive';
import ObligationsPending from './ObligationsPending';
import { fetchUserProfile } from '../api';

export default {
  name: 'ReportersList',

  components: {
    wip: WIP,
    envelopeArchive: EnvelopeArchive,
    obligationsPending: ObligationsPending,
  },

  data() {
    return {
      userProfile: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    fetchUserProfile()
      .then((response) => {
        let reportersTemp = [];
        this.userProfile = response.data;
        if (this.userProfile.reporters.length === 1) {
          this.$router.push({ name: 'Dashboard', params: { reporterId: this.userProfile.reporters[0].id } });
        }
      })
      .catch((e) => {
        console.log(e);
      });
  },

  methods: {
  },
};
</script>

<style>

</style>
