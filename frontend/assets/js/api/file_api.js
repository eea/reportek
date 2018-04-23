/* eslint-disable */
import axios from 'axios';
import tus from 'tus-js-client';
import { fetch, update, remove, filesURL, apiURL } from './config_api';


export function runEnvelopeFilesConvertScript(id, fileId, scriptId) {
  return axios({
    baseURL: apiURL,
    withCredentials: true,
    method: 'post',
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFTOKEN",
    url: `envelopes/${id}/files/${fileId}/run_conversion_script/`,
    responseType: 'arraybuffer',
    data: { convert_id: scriptId },
  })
}

export function updateFile(id, fileId, name) {
  return update(`envelopes/${id}/files/${fileId}/`, { name: name });
}

export function updateFileRestriction(id, fileId, restricted) {
  return update(`envelopes/${id}/files/${fileId}/`, { restricted: restricted });
}

export function removeFile(id, fileId) {
  return remove(`envelopes/${id}/files/${fileId}/`);
}

export function uploadFile(file, filename, fileId, token) {
  // Create a new tus upload
  return new Promise((resolve, reject) => {
    const upload = new tus.Upload(file.data,
      {
        endpoint: filesURL,
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
