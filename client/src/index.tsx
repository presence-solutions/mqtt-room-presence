import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter } from 'react-router-dom';
import { Provider as ReduxProvider } from 'react-redux';

import { store } from './store/store';
import App from './containers/App/App';
// import reportWebVitals from './reportWebVitals';

import { createClient, Provider as UrqlProvider } from 'urql';

const urqlClient = createClient({
  url: process.env.REACT_APP_GRAPHQL_URI!
});

ReactDOM.render(
  <React.StrictMode>
    <ReduxProvider store={store}>
      <BrowserRouter>
        <UrqlProvider value={urqlClient}>
          <App />
        </UrqlProvider>
      </BrowserRouter>
    </ReduxProvider>
  </React.StrictMode >,
  document.getElementById('root')
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals();
