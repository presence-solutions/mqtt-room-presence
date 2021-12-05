import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import Box from '@mui/material/Box';
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
import { getRooms, addRoom, editRoom, deleteRoom } from '../../../lib/api/rooms';
import PageTitle from '../../../components/PageTitle/PageTitle';
import RoomsModal from './RoomsModal';

export interface RoomsModalState {
  open: boolean,
  mode: 'add' | 'edit',
  roomId: number | null,
  initialValues: {
    roomName: string
  }
}

export default function RoomsPage() {
  const queryClient = useQueryClient();
  const fm = useFormatMessage();

  const [modalState, setModalState] = useState<RoomsModalState>({
    open: false,
    mode: 'add',
    roomId: null,
    initialValues: {
      roomName: ''
    }
  });

  const getRoomsResult = useQuery('rooms', getRooms);
  const rooms = getRoomsResult.data || [];

  const onMutationSucces = () => {
    queryClient.invalidateQueries('rooms');
    closeModal();
  };

  const addRoomMutation = useMutation(addRoom, {
    onSuccess: onMutationSucces
  });

  const editRoomMutation = useMutation(editRoom, {
    onSuccess: onMutationSucces
  });

  const deleteRoomMutation = useMutation(deleteRoom, {
    onSuccess: onMutationSucces
  });

  const onAddSubmit = (name: string) => {
    addRoomMutation.mutate({ name });
  };

  const onEditSubmit = (id: number, name: string) => {
    editRoomMutation.mutate({ id, name });
  };

  const deleteRoomHandler = (id: number) => {
    deleteRoomMutation.mutate({ id });
  };

  const openEditModal = (roomId: number) => {
    const room = rooms.find(r => r.id === roomId);

    if (room) {
      setModalState({
        open: true,
        mode: 'edit',
        roomId,
        initialValues: {
          roomName: room.name
        }
      });
    }
  };

  const onOpenAddModalClick = () => {
    setModalState({
      open: true,
      mode: 'add',
      roomId: null,
      initialValues: {
        roomName: ''
      }
    });
  };

  const closeModal = () => {
    setModalState({
      ...modalState,
      open: false
    });
  };

  return (
    <div>
      <PageTitle>{fm('RoomsPage_Title')}</PageTitle>

      <Box sx={{ px: { md: 8 }, mt: 2 }}>
        <TableContainer component={Paper}>
          <Table aria-label='rooms list'>
            <TableHead>
              <TableRow>
                <TableCell>{fm('RoomsPage_IdColumn')}</TableCell>
                <TableCell>{fm('RoomsPage_NameColumn')}</TableCell>
                <TableCell align='center' sx={{ p: 0 }}>
                  <Tooltip title={fm('RoomsPage_AddRoomTooltip')} placement='top'>
                    <IconButton
                      aria-label='edit'
                      sx={{ '&:hover': { cursor: 'pointer' } }}
                      onClick={onOpenAddModalClick}>
                      <AddIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {rooms.map(room => (
                <TableRow key={room.id} hover>
                  <TableCell>{room.id}</TableCell>
                  <TableCell>{room.name}</TableCell>
                  <TableCell align='center' sx={{ p: 0 }}>
                    <Tooltip title={fm('RoomsPage_EditRoomTooltip')} placement='top'>
                      <IconButton
                        aria-label='edit'
                        sx={{ '&:hover': { cursor: 'pointer' } }}
                        onClick={() => { openEditModal(room.id); }}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <RoomsModal
        {...modalState}
        onClose={closeModal}
        onAddSubmit={onAddSubmit}
        onEditSubmit={onEditSubmit}
        deleteHandler={deleteRoomHandler} />
    </div>
  );
}
