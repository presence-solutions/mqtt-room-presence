import { useCallback, useMemo } from 'react';
import { Outlet } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { ThemeProvider, createTheme } from '@mui/material/styles';

import { useFormatMessage } from '../../intl/helpers';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { setTheme } from '../../store/slices/commonSlice';
import { ThemeType } from '../../types/common';
import GlobalErrorModal from '../../containers/GlobalErrorModal/GlobalErrorModal';
import ThemeSwitch from '../../components/ThemeSwitch/ThemeSwitch';

type Props = {};

const Layout: React.VFC<Props> = () => {
  const fm = useFormatMessage();
  const dispatch = useAppDispatch();
  const { theme } = useAppSelector((state) => state.common);

  const themeConfig = useMemo(() => createTheme({
    palette: { mode: theme }
  }), [theme]);

  const onThemeSwitchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setTheme(e.target.checked ? ThemeType.dark : ThemeType.light));
  }, [dispatch]);

  return (
    <ThemeProvider theme={themeConfig}>
      <CssBaseline />

      <AppBar position='fixed'>
        <Container maxWidth='xl'>
          <Toolbar disableGutters>
            <Typography variant='h6' component='div' sx={{ flexGrow: 1 }}>
              {fm('App_Title')}
            </Typography>

            <ThemeSwitch
              checked={theme === ThemeType.dark}
              onChange={onThemeSwitchChange} />
          </Toolbar>
        </Container>
      </AppBar>

      <Box component='main'>
        <Toolbar />

        <Container maxWidth='xl'>
          <Outlet />
        </Container>
      </Box>

      <GlobalErrorModal />
    </ThemeProvider>
  );
};

export default Layout;
