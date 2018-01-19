import Vue from 'vue'
import Envelopes from '@/js/components/Envelopes'

describe('Envelopes.vue', () => {
  // Inspect the raw component options
  it('has a created hook', () => {
    expect(Envelopes.created).to.be.a('function')
  })
})
