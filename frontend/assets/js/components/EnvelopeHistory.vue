<template>
      <div class="sidebar-item">
        <h5>History</h5>
        <div class="history">          
          <div class="history-item mt-3 mb-3" v-for="(history, key, index) in envelopeHistory">
            <span v-if="index == Object.keys(envelopeHistory).length -1">
              <div class="state">{{history.from_state | capitalize}}</div>
              <div class="date btn-link">{{dateFormat(key)}}</div>
            </span>
            <span v-else-if="index != 0" :class="{ hidden: hiddenItems }">
                <div class="state">{{history.to_state | capitalize}}</div>
                <div class="date btn-link">{{dateFormat(key)}}</div>
            </span>
             <span v-else>
              <div class="state">{{history.to_state | capitalize}}</div>
              <div class="date btn-link">{{dateFormat(key)}}</div>
            </span>
          </div>
          <div v-if="hiddenItems == true" 
               id="show-more" 
               class="btn btn-link pb-3 pt-3" 
               @click="hiddenItems = false">
           +{{ Object.keys(envelopeHistory).length -2 }} versions
         </div>
        <div v-if="hiddenItems == false" 
               class="btn-link" 
               @click="hiddenItems = true">
           show less versions
         </div>
        </div>
      </div>
</template>

<script>
import { fetchEnvelopeHistory } from '../api';
export default {
  name: 'EnvelopeItem',
  
  components: {
    'history': History,
  },

  data() {
    return {
      envelopeHistory: null,
      hiddenItems: true,
    };
  },

  // Fetches posts when the component is created.
  created() {
    this.getEnvelopeHistory();
  },

  methods: {
    getEnvelopeHistory() {
      fetchEnvelopeHistory(this.$route.params.envelope_id)
        .then((response) => {
          this.envelopeHistory = response.data;
          console.log(this.envelopeHistory)
        });
    },

    dateFormat(date) {
      const options = { year: 'numeric', month: 'long', day: 'numeric', };
      const preFormatDate = new Date(date);
      return preFormatDate.toLocaleDateString('en-GB',options);
    },
  },

  filters: {
    capitalize: function (value) {
      if (!value) return ''
      value = value.toString()
      return value.charAt(0).toUpperCase() + value.slice(1)
    },
  },
}
</script>

<style lang="scss" scoped>
.history-item { 
  position: relative; 
  .state {
    font-weight: bold;
  }
}

.history-item {
  &:before {
    content:'sds';
  } 
}

.hidden {
  display: none;
}

.hidden:first-of-type {
  opacity: 0;
  display: block;
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
</style>
