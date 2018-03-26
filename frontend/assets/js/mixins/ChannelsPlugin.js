import ReconnectingWebSocket from 'reconnecting-websocket';
import { Observable } from 'rxjs/Observable';
import { Subject } from 'rxjs/Subject';
import 'rxjs/add/operator/multicast';

export default {
  // TODO implement a filtering of events (file/envelope)

  /**
   * will install the plugin
   * @param {Object} Vue 
   * @param {Object} channelOptions
   * @param {Boolean} channelOptions.debug
   * @param {number} channelOptions.reconnectInterval
   */
  install(Vue, channelOptions) {
    let observableSocket;
    let subscriptionSet = {};
    let self = this;

    /**
     * - will create the observable based on WebSocket
     * - it will make the connection, but until a subscribe is done, no message will be received
     * - it will make only one connection for now
     * @param {string} connection - ex: '/ws/envelopes/16'
     */
    Vue.prototype.$listen = function (connection) {
      console.log('channels observableSocket ', observableSocket);

      if(!observableSocket) {
        observableSocket = self.fromWebSocket(connection, channelOptions);
      }
    }

    /**
     * - it will make a new subscription every time it is called
     * - the subscribe actually starts the execution of listening
     * @param {Object} observer -  a set of callbacks
     * @param {requestCallback} observer.next - callback for valid message received
     * @param {requestCallback} observer.error - callback for error
     * @param {requestCallback} observer.complete - callback for completed stream
     * @param {string} subscriptionType - ex 'envelope', it will be used to create a subscription for each type
     */
    let subscribe = function (observer, subscriptionType) {
      let subscription = {};

      if(subscriptionSet[subscriptionType]) {
        console.warn('subscription already exists!!!')
        subscriptionSet[subscriptionType].unsubscribe();
      }
      subscriptionSet[subscriptionType] = observableSocket.subscribe(observer);
      console.log('channels subscribe subscriptionSet ', subscriptionSet);
    };

    /**
     * it unsubscribes and also removed the subscription from the set
     * @param {string} subscriptionType 
     */
    let unsubscribe = function (subscriptionType) {
      subscriptionSet[subscriptionType].unsubscribe();
      delete subscriptionSet[subscriptionType];
      console.log('channels unsubscribe subscriptionSet ', subscriptionSet);
    };

    Vue.mixin({
      methods: {
        subscribe,
        unsubscribe
      }
    });
  },

  /**
   * - will create the observable based on WebSocket
   * @param {string} address - ex: '/ws/envelopes/16'
   * @param {string} options - debug, reconnectInterval
   * @returns {Object} observable - that was created from the websocket
   */
  fromWebSocket(address, options) {
    const webSocket = this.connect(address, [], options);

    // Handle the data
    const observable = Observable.create(function (obs) {
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

    return observable;
  },

  /**
   * Connect to the websocket server
   * @param {String} [url] The url of the websocket. Defaults to
   * `window.location.host`
   * @param {String[]|String} [protocols] Optional string or array of protocols.
   * @param {Object} options Object of options for [`reconnecting-websocket`](https://github.com/joewalnes/reconnecting-websocket#options-1).
   * @returns {Object} ReconnectingWebSocket - that was created from the websocket
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
