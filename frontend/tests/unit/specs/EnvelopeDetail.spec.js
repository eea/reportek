import Vue from 'vue'
import EnvelopeDetail from '@/js/components/EnvelopeDetail'

describe('EnvelopeDetail.vue', () => {
  // Inspect the raw component options
  it('has a created hook', () => {
    expect(EnvelopeDetail.created).to.be.a('function')
  })
})
