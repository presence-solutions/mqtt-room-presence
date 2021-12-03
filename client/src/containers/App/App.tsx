import { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import type { LocaleMessages } from '../../intl/helpers';
import { ThemeType } from '../../types/common';
import { useAppSelector } from '../../store/hooks';
import { IntlProvider, loadMessages } from '../../intl/helpers';
import { defaultLocale } from '../../lib/constants/common';
import Layout from '../Layout/Layout';
import HomePage from '../HomePage/HomePage';
import RoomsPage from '../HomePage/RoomsPage/RoomsPage';
import DevicesPage from '../HomePage/DevicesPage';
import ScannersPage from '../HomePage/ScannersPage';
import NotFoundPage from '../NotFoundPage/NotFoundPage';

const lightTheme = createTheme({
  palette: {
    mode: ThemeType.light
  }
});

const darkTheme = createTheme({
  palette: {
    mode: ThemeType.dark
  }
});

export default function App() {
  const [messages, setMessages] = useState<LocaleMessages | null>(null);
  const locale = defaultLocale;

  useEffect(() => {
    loadMessages(locale).then(setMessages);
  }, [locale]);

  const theme = useAppSelector((state) => state.common.theme);
  const themeConfig = theme === ThemeType.light ? lightTheme : darkTheme;

  if (messages) {
    return (
      <IntlProvider locale={locale} messages={messages}>
        <ThemeProvider theme={themeConfig}>
          <Routes>
            <Route element={<Layout theme={theme} />}>
              <Route path='/' element={<HomePage />}>
                <Route path='rooms' element={<RoomsPage />} />
                <Route path='devices' element={<DevicesPage />} />
                <Route path='scanners' element={<ScannersPage />} />
              </Route>
              <Route path='*' element={<NotFoundPage />} />
            </Route>
          </Routes>
        </ThemeProvider>
      </IntlProvider>
    );
  }

  return null;
}
