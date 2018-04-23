/* eslint-disable */
import { fetch, post } from './config_api';

export function fetchEnvelopes() {
  return fetch('envelopes/');
}

export function fetchEnvelope(id) {
  return fetch(`envelopes/${id}/`);
}

export function createEnvelope(envelope) {
  return post(`envelopes/`,
    {
      name: envelope.name,
      reporter: envelope.reporter,
      obligation_spec: envelope.obligationSpec,
      reporting_cycle: envelope.reportingCycle,
      description: envelope.description,
      coverage_note: envelope.coverage_note,
    });
}

export function fetchEnvelopeToken(id) {
  return post(`envelopes/${id}/token/`);
}

export function fetchEnvelopeFiles(id) {
  return fetch(`envelopes/${id}/files/`);
}

export function fetchEnvelopeFile(envelopeId, fileId) {
  return fetch(`envelopes/${envelopeId}/files/${fileId}/`);
}

export function fetchEnvelopeWorkflow(id) {
  return fetch(`envelopes/${id}/workflow_graph/`);
}

export function fetchEnvelopeFilesQAScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/qa_scripts/`);
}

export function runEnvelopeFilesQAScript(id, fileId, scriptId) {
  return post(`envelopes/${id}/files/${fileId}/run_qa_script/`, { script_id: scriptId });
}

export function fetchEnvelopeFilesConvertScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/conversion_scripts/`);
}
export function fetchEnvelopeHistory(id) {
  return fetch(`envelopes/${id}/history/`);
}

export function fetchEnvelopeFeedback(id) {
  return fetch(`envelopes/${id}/feedback/`);
}

export function runEnvelopeTransition(id, transitionName) {
  return post(`envelopes/${id}/transition/`, { transition_name: transitionName });
}

export function fetchObligationsPending(reporterId) {
  return fetch(`workspace-reporter/${reporterId}/pending/`);
}

export function fetchWipEnvelopes(reporterId) {
  return fetch(`workspace-reporter/${reporterId}/wip/`);
}

export function fetchArchiveEnvelopes(reporterId) {
  return fetch(`workspace-reporter/${reporterId}/archive/`);
}
