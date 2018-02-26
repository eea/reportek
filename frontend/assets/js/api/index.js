/* eslint-disable */
import axios from 'axios';

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

const logRequests = process.env.NODE_ENV === 'development';
const api = axios.create({
  baseURL: 'http://localhost:8000/api/0.1/',
  withCredentials: true,
})

function fetch(path) {
  logRequests && console.log(`fetching ${path}...`);

  return api.get(path);
}

function post(path, data) {
  logRequests && console.log(`posting ${path} with data ${data}...`);

  return api.post(path, data);
}

function update(path, data) {
  logRequests && console.log(`patching ${path} with data ${data}...`);

  return api.patch(path, data);
}

function remove(path) {
  logRequests && console.log(`removig ${path} ...`);

  return api.delete(path);
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

export function fetchEnvelopeWorkflow(id) {
  return fetch(`envelopes/${id}/workflow_graph/`);
}

export function fetchEnvelopeFilesQAScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/qa_scripts/`);
}

export function runEnvelopeFilesQAScript(id, fileId, scriptId) {
  return post(`envelopes/${id}/files/${fileId}/run_qa_script/`, {script_id: scriptId});
}

export function fetchEnvelopeFilesConvertScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/conversion_scripts/`);
}

export function runEnvelopeFilesConvertScript(id, fileId, scriptId) {
// Using the post method doesn't work. We have to use a new axios instance
  return  axios({
            baseURL: 'http://localhost:8000/api/0.1/',
            withCredentials: true,
            method:'post',
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFTOKEN",
            url:`envelopes/${id}/files/${fileId}/run_conversion_script/`,
            responseType:'arraybuffer',
            data: {convert_id: scriptId}
          })
}

export function updateFile(id, fileId, name) {
  return update(`envelopes/${id}/files/${fileId}/`, {name: name});
}

export function removeFile(id, fileId) {
  return remove(`envelopes/${id}/files/${fileId}/`);
}

export function fetchEnvelopeHistory(id) {
  return fetch(`envelopes/${id}/history/`);
}

export function fetchEnvelopeFeedback(id) {
  return fetch(`envelopes/${id}/feedback/`);
}

export function runEnvelopeTransition(id, transitionName) {
  return post(`envelopes/${id}/transition/`, {transition_name: transitionName});
}

export function fetchUserProfile() {
  return fetch(`workspace-profile/`);
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

