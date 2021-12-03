import { Outlet } from 'react-router';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import BedIcon from '@mui/icons-material/Bed';
import DevicesIcon from '@mui/icons-material/Devices';
import CastConnectedIcon from '@mui/icons-material/CastConnected';

import { useFormatMessage } from '../../intl/helpers';
import SideBarLink from '../../components/SideBarLink/SideBarLink';

export default function HomePage() {
  const formatMessage = useFormatMessage();

  return (
    <Grid container columns={16}>
      <Grid item xs={16} md={4} lg={3}>
        <List component='nav' aria-label='side bar navigation'>
          <SideBarLink
            to='rooms'
            text={formatMessage('HomePage_RoomsLink')}
            icon={<BedIcon />}
          />
          <SideBarLink
            to='devices'
            text={formatMessage('HomePage_DevicesLink')}
            icon={<DevicesIcon />}
          />
          <SideBarLink
            to='scanners'
            text={formatMessage('HomePage_ScannersLink')}
            icon={<CastConnectedIcon />}
          />
        </List>
      </Grid>

      <Grid item xs sx={{ py: 1, pl: { xs: 0, md: 1 } }}>
        <Outlet />
      </Grid>
    </Grid>
  );
}
