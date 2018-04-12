/* eslint-disable */
import axios from 'axios';
import tus from 'tus-js-client';

const logRequests = process.env.NODE_ENV === 'development';

const BACKEND_HOST = 'localhost';
const BACKEND_PORT = 8000;
const _backend_host = process.env.BACKEND_HOST || BACKEND_HOST;
const _backend_port = process.env.BACKEND_PORT && Number(process.env.BACKEND_PORT) || BACKEND_PORT;

const TUSD_HOST = 'localhost';
const TUSD_PORT = 1080;
const _tusd_host = process.env.TUSD_HOST || TUSD_HOST;
const _tusd_port = process.env.TUSD_PORT && Number(process.env.TUSD_PORT) || TUSD_PORT;


const api = axios.create({
  baseURL: `http://${_backend_host}:${_backend_port}/api/0.1/`,
  withCredentials: true,
});

api.defaults.xsrfHeaderName = "X-CSRFTOKEN";
api.defaults.xsrfCookieName = "csrftoken";

function checkAuth() {
  if(!api.defaults.headers['authorization'] && getCookie('authToken')) {
    api.defaults.headers.authorization = 'token ' + getCookie('authToken');
  }
}

function fetch(path) {
  logRequests && console.log(`fetching ${path}...`);
  checkAuth();
  return api.get(path);
}

function post(path, data) {
  logRequests && console.log(`posting ${path} with data ${data}...`);
  checkAuth();
  return api.post(path, data);
}

function update(path, data) {
  logRequests && console.log(`patching ${path} with data ${data}...`);
  checkAuth();
  return api.patch(path, data);
}

function remove(path) {
  logRequests && console.log(`removig ${path} ...`);
  checkAuth();
  return api.delete(path);
}

export function removeLoginToken() {

  return new Promise((resolve, reject) => {
    remove(`/auth-token/${getCookie('authToken')}`)
      .then((response) => {
        console.log('delete');
        delete api.defaults.headers.authorization;
        resolve();
      })
      .catch((error) => {
        reject(error);
      });
  })
}

function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function(el) {
    let [k,v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie[name];
}

export function getLoginToken(username,password) {

  return new Promise((resolve, reject) => {
    post('/auth-token/', {'username': username, 'password': password})
      .then((response) => {
        console.log('get login token');

        api.defaults.headers.authorization = 'token ' + response.data.token;
        resolve(response);
      })
      .catch((error) => {
        reject(error);
      });
  });
}

export function fetchEnvelopes() {
  return fetch('envelopes/');
}

export function fetchEnvelope(id) {
  return fetch(`envelopes/${id}/`);
}

export function activateEnvelope(id) {
  return post(`envelopes/${id}/assign/`);
}

export function deactivateEnvelope(id) {
  return post(`envelopes/${id}/unassign/`);
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
  return post(`envelopes/${id}/files/${fileId}/run_qa_script/`, {script_id: scriptId});
}

export function fetchEnvelopeFilesConvertScripts(id, fileId) {
  return fetch(`envelopes/${id}/files/${fileId}/conversion_scripts/`);
}

export function runEnvelopeFilesConvertScript(id, fileId, scriptId) {

  return  axios({
            baseURL: `http://${_backend_host}:${_backend_port}/api/0.1/`,
            withCredentials: true,
            method:'post',
            xsrfCookieName: "csrftoken",
            xsrfHeaderName: "X-CSRFTOKEN",
            url:`envelopes/${id}/files/${fileId}/run_conversion_script/`,
            responseType:'arraybuffer',
            data: {convert_id: scriptId},
          })
}

export function updateFile(id, fileId, name) {
  return update(`envelopes/${id}/files/${fileId}/`, {name: name});
}

export function updateFileRestriction(id, fileId, restricted) {
  return update(`envelopes/${id}/files/${fileId}/`, {restricted: restricted});
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

export function uploadFile(file, filename, fileId, token) {
  // Create a new tus upload
  return new Promise((resolve, reject) => {
    const upload = new tus.Upload(file.data,
      {
        endpoint: `http://${_tusd_host}:${_tusd_port}/files/`,
        metadata: {
          token,
          filename,
          fileId,
        },
        retryDelays: [0, 1000, 3000, 5000],
        onError: function onError(error) {
          console.log('Failed because: ', error);
          reject(error);
        },
        onProgress: function onProgress(bytesUploaded, bytesTotal) {
          file.percentage = parseInt(((bytesUploaded / bytesTotal) * 100).toFixed(2), 10);
          console.log(bytesUploaded, bytesTotal, file.percentage, '%');
        },
        onSuccess: function onSuccess() {
          console.log('Download %s from %s', upload.file.name, upload.url);
          resolve(
            {
              fileName: upload.file.name,
              uploadUrl: upload.url,
            },
          );
        },
      });
    // Start the upload
    upload.start();
  });
}

export function fetchObligation(id) {
  return fetch(`/obligations/${id}/`);
}
