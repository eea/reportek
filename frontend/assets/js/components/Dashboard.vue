<template>
  <div>
    <div v-if="userProfile && userProfile.reporters.length > 1">
      <b-form-select
        :options="reporters"
        v-model="selectedReporterId"
        v-show="userProfile.reporters.length > 1"
      >
      </b-form-select>
    </div>

    <div v-if="selectedReporterId">
      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesWIP', params: { reporterId: selectedReporterId, spec: 1 } }"
      >
        WIP
      </router-link>

      <router-link
        class="nav-link"
        :to="{ name: 'EnvelopesArchive', params: { reporterId: selectedReporterId, spec: 1 } }"
      >
        Archive
      </router-link>
      
      <obligations-pending :reporterId="selectedReporterId"></obligations-pending>
    </div>

    <h1 v-if="userProfile && userProfile.reporters.length === 0">User doesn't have a reporter</h1>
  </div>
</template>

<script>
import WIP from './EnvelopesWIP';
import EnvelopeArchive from './EnvelopesArchive';
import ObligationsPending from './ObligationsPending';
import { fetchUserProfile } from '../api';

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
      userProfile: null,
      reporters: [],
      selectedReporterId: null,
    };
  },

  // Fetches posts when the component is created.
  created() {
    fetchUserProfile()
      .then((response) => {
        let reportersTemp = [{ value: null, text: 'Please select reporter' }];
        this.userProfile = response.data;

        response.data.reporters.map((reporter) => {
          reportersTemp.push({ value: reporter.id, text: reporter.name });
          return reporter;
        });
        this.reporters = reportersTemp.slice();

        if (this.reporters.length === 1) {
          this.selectedReporterId = this.reporters[0];
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
