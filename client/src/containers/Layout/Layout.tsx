import { useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import { useAppDispatch } from '../../store/hooks';
import { setTheme } from '../../store/slices/commonSlice';
import { ThemeType } from '../../types/common';
import ThemeSwitch from '../../components/ThemeSwitch/ThemeSwitch';

type Props = {
  theme: ThemeType
};

const appTitle = 'Room Presence';

export default function Layout({ theme }: Props) {
  const dispatch = useAppDispatch();

  const onThemeSwitchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setTheme(e.target.checked ? ThemeType.dark : ThemeType.light));
  }, [dispatch]);

  return (
    <>
      <CssBaseline />

      <AppBar position='fixed'>
        <Container maxWidth='xl'>
          <Toolbar disableGutters>
            <Typography variant='h6' component='div' sx={{ flexGrow: 1 }}>
              {appTitle}
            </Typography>

            <ThemeSwitch
              checked={theme === ThemeType.dark}
              onChange={onThemeSwitchChange}
            />
          </Toolbar>
        </Container>
      </AppBar>

      <Box component='main'>
        <Toolbar />

        <Container maxWidth='xl'>
          <Outlet />
        </Container>
      </Box>
    </>
  );
}
