/* eslint-disable */
import axios from 'axios';

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

const logRequests = process.env.NODE_ENV === 'development';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/0.1/',
  withCredentials: true,
})

function fetch(child) {
  logRequests && console.log(`fetching ${child}...`);

  return api.get(child);
}

function post(child, data) {
  logRequests && console.log(`posting ${child} with data ${data}...`);

  return api.post(child, data);
}

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
  });
}

export function fetchEnvelopeToken(id) {
  return post(`envelopes/${id}/token/`);
}

export function fetchEnvelopeFiles(id) {
  return fetch(`envelopes/${id}/files/`);
}

export function fetchEnvelopeFilesQAScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/qa_scripts`);
}

export function runEnvelopeFilesQAScript(id, fileId, script_id) {
  return post(`envelopes/${id}/files/${fileId}/run_qa_script/`, {script_id: script_id});
}

export function fetchEnvelopeHistory(id) {
  return fetch(`envelopes/${id}/history/`);
}

export function fetchEnvelopeFeedback(id) {
  return fetch(`envelopes/${id}/feedback/`);
}

export function runEnvelopeTransition(id, transition_name) {
  return post(`envelopes/${id}/transition/`, {transition_name: transition_name});
}

export function fetchObligations() {
  return fetch(`obligations/`);
}

export function fetchReporters() {
  return fetch(`reporters/`);
}

export function fetchObligationSpecs() {
  return fetch(`obligation-spec-reporters/`);
}

export function fetchReportingCycles() {
  return fetch(`reporting-cycles/`);
}

export function fetchWipEnvelopes() {
  return fetchEnvelopes();
}


export function fetchArchiveEnvelopes() {
  return fetchEnvelopes();
}

export function fetchObligationsPending() {
  return fetch(`obligations/14/`);
}
