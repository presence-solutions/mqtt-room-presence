import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';

import { IntlProvider, loadMessages } from '../../intl/helpers';
import { defaultLocale } from '../../lib/constants/common';
import Layout from '../Layout/Layout';
import HomePage from '../HomePage/HomePage';
import RoomsPage from '../HomePage/RoomsPage/RoomsPage';
import DevicesPage from '../HomePage/DevicesPage/DevicesPage';
import ScannersPage from '../HomePage/ScannersPage';
import NotFoundPage from '../NotFoundPage/NotFoundPage';

import type { LocaleMessages } from '../../intl/helpers';

const App: React.VFC = () => {
  const [messages, setMessages] = useState<LocaleMessages | null>(null);
  const locale = defaultLocale;

  useEffect(() => {
    loadMessages(locale).then(setMessages);
  }, [locale]);

  if (!messages) {
    return null;
  }

  return (
    <IntlProvider locale={locale} messages={messages}>
      <Routes>
        <Route element={<Layout />}>
          <Route path='/' element={<HomePage />}>
            <Route path='rooms' element={<RoomsPage />} />
            <Route path='devices' element={<DevicesPage />} />
            <Route path='scanners' element={<ScannersPage />} />
          </Route>
          <Route path='*' element={<NotFoundPage />} />
        </Route>
      </Routes>
    </IntlProvider>
  );
};

export default App;
