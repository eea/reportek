import Vue from 'vue'
import EnvelopeItem from '@/js/components/EnvelopeItem'

describe('EnvelopeItem.vue', () => {
  // Inspect the raw component options
  it('has a created hook', () => {
    expect(EnvelopeItem.created).to.be.a('function')
  })
})
