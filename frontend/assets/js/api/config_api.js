/* eslint-disable */
import axios from 'axios';

const logRequests = process.env.NODE_ENV === 'development';

const BACKEND_HOST = 'localhost';
const BACKEND_PORT = 8000;
const _backend_host = process.env.BACKEND_HOST || BACKEND_HOST;
const _backend_port = process.env.BACKEND_PORT && Number(process.env.BACKEND_PORT) || BACKEND_PORT;

const TUSD_HOST = 'localhost';
const TUSD_PORT = 1080;
const _tusd_host = process.env.TUSD_HOST || TUSD_HOST;
const _tusd_port = process.env.TUSD_PORT && Number(process.env.TUSD_PORT) || TUSD_PORT;
const apiURL = `http://${_backend_host}:${_backend_port}/api/0.1/`;
const filesURL = `http://${_tusd_host}:${_tusd_port}/files/`;

const api = axios.create({
  baseURL: apiURL,
  withCredentials: true,
});

api.defaults.xsrfHeaderName = "X-CSRFTOKEN";
api.defaults.xsrfCookieName = "csrftoken";

function checkAuth() {
  if (!api.defaults.headers['authorization'] && getCookie('authToken')) {
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

function getCookie(name) {
  let cookie = {};
  document.cookie.split(';').forEach(function (el) {
    let [k, v] = el.split('=');
    cookie[k.trim()] = v;
  })
  return cookie[name];
}

export { apiURL, filesURL, api, fetch, post, update, remove, getCookie };
