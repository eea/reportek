import ReconnectingWebSocket from 'reconnecting-websocket';
import { Observable } from 'rxjs/Observable';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

export default {
  // TODO implement a filtering of events (file/envelope)

  install(Vue, channelOptions) {
    let socketSubject;
    let self = this;

    Vue.prototype.$listen = function (connection) {
      console.log('channels socketSubject ', socketSubject);

      if(!socketSubject) {
        socketSubject = self.fromWebSocket(connection, channelOptions);
      }
    }

    let subscribe = function (observer) {
      // Receive data
      socketSubject.subscribe(observer);
    };

    let unsubscribe = function () {
      socketSubject.unsubscribe();
      socketSubject = null;
      console.log('channels socketSubject after unsubscribe ', socketSubject);
    };

    Vue.mixin({
      methods: {
        subscribe,
        unsubscribe
      }
    });
  },

  fromWebSocket(address, options) {
    const webSocket = this.connect(address, [], options);

    // Handle the data
    const osbervable = Observable.create(function (obs) {
      // Handle messages  
      webSocket.onmessage = (message) => {
        const data = JSON.parse(message.data);

        obs.next(data);
      }
      webSocket.onerror = obs.error.bind(obs);
      webSocket.onclose = obs.complete.bind(obs);

      // Return way to unsubscribe
      return webSocket.close.bind(webSocket);
    });

    const observer =  {
      next(x) {
      },
      error(error) {
      },
      complete() {
      }
    };

    return BehaviorSubject.create(observer, osbervable);
  },

  /**
   * Connect to the websocket server
   *
   * @param {String} [url] The url of the websocket. Defaults to
   * `window.location.host`
   * @param {String[]|String} [protocols] Optional string or array of protocols.
   * @param {Object} options Object of options for [`reconnecting-websocket`](https://github.com/joewalnes/reconnecting-websocket#options-1).
   */
  connect(url, protocols, options) {
    let _url;
    // Use wss:// if running on https://
    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const base_url = `${scheme}://${window.location.host}`;
    if (url === undefined) {
      _url = base_url;
    } else {
      // Support relative URLs
      if (url[0] == '/') {
        _url = `${base_url}${url}`;
      } else {
        _url = url;
      }
    }
    return new ReconnectingWebSocket(_url, protocols, options);
  }
}
