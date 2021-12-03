import { useQuery } from 'react-query';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import TableContainer from '@mui/material/TableContainer';
import Table from '@mui/material/Table';
import TableHead from '@mui/material/TableHead';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';

import { useFormatMessage } from '../../../intl/helpers';
import { getRooms } from '../../../lib/api/rooms';

export default function RoomsPage() {
  const formatMessage = useFormatMessage();

  const { isLoading, isError, data, error } = useQuery('rooms', getRooms);

  return (
    <div>
      <Typography variant='h4' component='h1' align='center' sx={{ mt: { md: 1 } }}>
        {formatMessage('RoomsPage_Title')}
      </Typography>

      {data &&
        <Box sx={{ px: { md: 8 }, mt: 2 }}>
          <TableContainer component={Paper}>
            <Table aria-label='rooms list'>
              <TableHead>
                <TableRow>
                  <TableCell>{formatMessage('RoomsPage_IdColumn')}</TableCell>
                  <TableCell>{formatMessage('RoomsPage_NameColumn')}</TableCell>
                  <TableCell align='center' sx={{ p: 0 }}>
                    <Tooltip title={formatMessage('RoomsPage_AddRoomTooltip')} placement='top'>
                      <IconButton
                        aria-label='edit'
                        sx={{ '&:hover': { cursor: 'pointer' } }}
                      >
                        <AddIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {
                  data.data.map(room => (
                    <TableRow key={room.id} hover>
                      <TableCell>{room.id}</TableCell>
                      <TableCell>{room.name}</TableCell>
                      <TableCell align='center' sx={{ p: 0 }}>
                        <Tooltip title={formatMessage('RoomsPage_EditRoomTooltip')} placement='top'>
                          <IconButton
                            aria-label='edit'
                            sx={{ '&:hover': { cursor: 'pointer' } }}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                }
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      }
    </div>
  );
}
