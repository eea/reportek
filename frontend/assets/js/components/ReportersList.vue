<template>
  <div class="reporters-list" v-if="userProfile">
    <div class="reporters-list-body">
        <div class="reporters-list-header">
        <p>
          You have permission to report for multiple countries
        </p>
        <!-- <h2>Which country are you reporting for ?</h2> -->
        <h2>{{ $t('country_question') }}</h2>
        </div>
      <ul >
        <li
          v-for="reporter in userProfile.reporters"
          :key="reporter.id"
        >
          <router-link
            class="nav-link"
            :to="{name:'Dashboard', params: {reporterId: `${reporter.id}`}}"
          >
            <span v-bind:class="[countryFlag(reporter.abbr), 'flag-icon']"></span><span>{{reporter.name}}</span>
          </router-link>
        </li>
      </ul>
      <p>
        Logged in as {{userProfile.username}}
      </p>
      <p>
        Having trouble? Contact <a href="#">helpdesk@eionet.europa.eu</a>
      </p>
    </div>
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
    this.getUserProfile();
  },

  methods: {
    getUserProfile() {
      fetchUserProfile()
        .then((response) => {
          this.userProfile = response.data;
          if (this.userProfile.reporters.length === 1) {
            this.$router.push({ name: 'Dashboard', params: { reporterId: this.userProfile.reporters[0].id } });
          }
        })
        .catch((e) => {
          console.log(e);
        });
    },

    countryFlag(countryAbbr) {
      return 'flag-icon-' + countryAbbr.toLowerCase();
    },
  },
};
</script>

<style lang="scss" scoped>

.reporters-list {
  display: flex;
  justify-content:center;
  height: calc(100vh - 64px);
  align-items: center;
  .reporters-list-body {
    width: 50%;
    max-width: 400px;
    margin: auto;
    > * {
      margin: 4rem 0;
    }
    ul {
      list-style-type: none;
      padding-left: 0;
      .flag-icon {
        width: 90px;
        height: 50px;
        margin-right: 1rem;
      }
      li {
        transition: all 150ms;
        display: block;
        border-radius: 3px;
        &:hover {
          box-shadow: 1px 1px 3px #aaa;
        }
      }
      a {
        display: flex;
        // justify-content: flex-start
        align-items: center;
        font-size: 2rem;
        font-size: 1.2rem;
      }
    }
  }
}
</style>
