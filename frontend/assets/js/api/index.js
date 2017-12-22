import axios from 'axios';

const logRequests = process.env.NODE_ENV === 'development';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/0.1/',
  withCredentials: true,
})

function fetch(child) {
  logRequests && console.log(`fetching ${child}...`);

  return api.get(child);
}

export function fetchEnvelopes() {
  return fetch(`envelopes/`);
}

export function fetchEnvelopeItem(id) {
  return fetch(`envelopes/${id}`);
}

export function fetchEnvelopeFiles(id) {
  return fetch(`envelopes/${id}/files`);
}
