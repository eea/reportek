<template>
  <div
    v-if="isItEmpty(envelopeHistory)"
    class="sidebar-item"
  >
    <h5>History</h5>
    <div class="history ">
      <div
        class="history-item"
        v-for="(history, key, index) in envelopeHistory"
        :key="key"
      >
        <span
          :class="[{ mb5 : hiddenItems }, 'mb-3 mt-3']"
          v-if="index == 0"
        >
          <div class="state">{{history.from_state | capitalize}}</div>
          <div class="date btn-link">{{formatDate(key)}}</div>
        </span>
        <span
          class="mt-3 mb-3"
          v-else
          :class="{ hidden: hiddenItems }">
            <div class="state">{{history.to_state | capitalize}}</div>
            <div class="date btn-link">{{formatDate(key)}}</div>
        </span>
      </div>
      <div class="history-item">
        <span class="mb-3 mt-3">
          <div class="state">Draaaaft</div>
          <div class="date btn-link">{{formatDate(created_at)}}</div>
        </span>
      </div>
      <div
        v-if="hiddenItems == true"
        id="show-more"
        class="btn btn-link pb-3 pt-3"
        @click="hiddenItems = false"
      >
        +{{ countContainedKeys(envelopeHistory) }} states
      </div>
    <div
      v-if="hiddenItems == false"
      class="btn-link"
      @click="hiddenItems = true"
    >
        show less states
      </div>
    </div>
  </div>
</template>

<script>
import { fetchEnvelopeHistory } from '../api';
import { dateFormat, capitalize } from '../utils/UtilityFunctions';


export default {
  name: 'EnvelopeHistory',

  components: {
    history: History,
  },

  filters: {
    capitalize
  },

  data() {
    return {
      envelopeHistory: null,
      hiddenItems: true,
    };
  },

  props: ['created_at'],

  // Fetches posts when the component is created.
  created() {
    this.getEnvelopeHistory();
  },

  updated(){
    if(Object.keys(this.envelopeHistory).length <= 2) {
      this.hiddenItems = false;
    }
  },

  methods: {
    getEnvelopeHistory() {
      fetchEnvelopeHistory(this.$route.params.envelope_id)
        .then((response) => {
          this.envelopeHistory = response.data;
        });
    },

    isItEmpty(item) {
      return (
        item !== null
        && typeof item === 'object'
        && Object.keys(item).length !== 0
      );
    },

    formatDate(date,count){
      return dateFormat(date,count)
    },

    countContainedKeys(obj) {
      return Object.keys(obj).length - 2;
    },
  },
};
</script>

<style lang="scss" scoped>
.history {
  .history-item {
     &:nth-last-of-type(2) {
          span:before {
            content:'';
            width: 15px;
            height: 15px;
            position: absolute;
            top: 40%;
            // transform: translateY(-50%);
            left: -6px;
            border: 2px solid rgba(0,0,0,.15);
            border-radius: 5rem;
          }
          span:after {
            content: '';
            height: calc(50% + 6px);
            position: absolute;
            top: -10px;
            left: 0px;
            border: 1px solid rgba(0, 0, 0, 0.15);
          }
        }
      &:first-of-type{
         span:before {
            content:'';
            width: 15px;
            height: 15px;
            position: absolute;
            top: 40%;
            // transform: translateY(-50%);
            left: -6px;
            border: 2px solid rgba(0,0,0,.15);
            border-radius: 5rem;
          }
          span:after {
            content:'';
            height: 50%;
            position: absolute;
            top: calc(40% + 15px);
            left: 0px;
            border: 1px solid rgba(0,0,0,.15);
          }
        }
      span {
        display: block;
        position: relative;
        padding-left: 1.5rem;
        .state {
          font-weight: bold;
        }
        &:after {
         content: '';
          height: 100%;
          position: absolute;
          top: 0;
          left: 0px;
          border: 1px solid rgba(0, 0, 0, 0.15);
        }


    }
  }
}

.hidden {
  display: none!important;
}


.history {
  position: relative;
}

#show-more {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    border-top: 1px solid rgba(0,0,0,.15);
    border-bottom: 1px solid rgba(0,0,0,.15);
    border-left: 2px solid rgba(0,0,0,.15);
    border-left-style: dashed;
    width: 100%;
    text-align: left;
}

.btn-link {
  cursor: pointer;
}
.mb5 {
  margin-bottom: 5rem!important;
}

</style>
