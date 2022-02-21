import { useEffect, useMemo, useState } from 'react';
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
import CircularProgress from '@mui/material/CircularProgress';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';

import { useFormatMessage } from '../../../intl/helpers';
import {
  useGetAllRoomsQuery,
  useAddRoomMutation,
  useUpdateRoomMutation,
  useRemoveRoomMutation
} from '../../../generated/graphql';
import { useAppDispatch } from '../../../store/hooks';
import { setGlobalError } from '../../../store/slices/commonSlice';
import { parseGlobalError } from '../../../lib/utility/globalError';
import { sortArrayByStringId } from '../../../lib/utility/sortArray';
import { TYPE_ROOM } from '../../../lib/constants/graphql';
import PageTitle from '../../../components/PageTitle/PageTitle';
import RoomsModal from './RoomsModal';

import type { NewRoomInput, UpdateRoomInput } from '../../../generated/graphql';

export type RoomsModalInitialValues = {
  name: string
};

type RoomsModalState = {
  open: boolean,
  mode: 'add' | 'edit',
  roomId: string | null,
  initialValues: RoomsModalInitialValues
};

type Props = {};

const defaultModalState: RoomsModalState = {
  open: false,
  mode: 'add',
  roomId: null,
  initialValues: {
    name: ''
  }
};

const sideColumnWidth = '64px';

const RoomsPage: React.VFC<Props> = () => {
  const dispatch = useAppDispatch();
  const fm = useFormatMessage();

  const [modalState, setModalState] = useState<RoomsModalState>({ ...defaultModalState });

  // Use additional typenames to fix empty lists not updating after first mutation
  const context = useMemo(() => ({ additionalTypenames: [TYPE_ROOM] }), []);
  const [roomsResult] = useGetAllRoomsQuery({ context });

  const [, addRoom] = useAddRoomMutation();
  const [, updateRoom] = useUpdateRoomMutation();
  const [, removeRoom] = useRemoveRoomMutation();

  const rooms = useMemo(() => {
    return roomsResult.data ? sortArrayByStringId(roomsResult.data.allRooms) : [];
  }, [roomsResult.data]);

  const showSpinner = roomsResult.fetching && rooms.length === 0;

  const showGlobalError = (e: Error) => {
    dispatch(setGlobalError(parseGlobalError(e)));
  };

  useEffect(() => {
    if (roomsResult.error) {
      showGlobalError(roomsResult.error);
    }
  });

  const onAddRoomClick = () => {
    setModalState({
      ...defaultModalState,
      open: true
    });
  };

  const onEditRoomClick = (roomId: string) => {
    const room = rooms.find(r => r.id === roomId);

    if (room) {
      setModalState({
        open: true,
        mode: 'edit',
        roomId,
        initialValues: {
          name: room.name || ''
        }
      });
    }
  };

  const onAddRoom = (newRoom: NewRoomInput) => {
    addRoom({ newRoom }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      }
    });
  };

  const onEditRoom = (room: UpdateRoomInput) => {
    const oldRoom = rooms.find(r => r.id === room.id);

    if (oldRoom) {
      room.scanners = oldRoom.scanners?.map(scanner => scanner.id!);

      updateRoom({ room }).then((result) => {
        closeModal();

        if (result.error) {
          showGlobalError(result.error);
        }
      });
    }
  };

  const deleteRoom = (roomId: string) => {
    removeRoom({ roomId }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      }
    });
  };

  const closeModal = () => {
    setModalState(prevState => ({
      ...prevState,
      open: false
    }));
  };

  return (
    <div>
      <PageTitle>{fm('RoomsPage_Title')}</PageTitle>

      <Box sx={{ px: { md: 8 }, mt: 2 }}>
        <TableContainer component={Paper}>
          <Table aria-label='rooms list' sx={{ borderCollapse: 'separate' }}>
            <TableHead>
              <TableRow>
                <TableCell align='center' sx={{ width: sideColumnWidth }}>
                  {fm('RoomsPage_IdColumn')}
                </TableCell>
                <TableCell>{fm('RoomsPage_NameColumn')}</TableCell>
                <TableCell align='center' sx={{ p: 0, width: sideColumnWidth }}>
                  <Tooltip title={fm('RoomsPage_AddRoomTooltip')} placement='top'>
                    <IconButton
                      aria-label='add room'
                      sx={{ '&:hover': { cursor: 'pointer' } }}
                      onClick={onAddRoomClick}>
                      <AddIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {rooms.map(room => (
                <TableRow key={room.id} hover>
                  <TableCell align='center'>{room.id}</TableCell>
                  <TableCell>{room.name}</TableCell>
                  <TableCell align='center' sx={{ p: 0 }}>
                    <Tooltip title={fm('RoomsPage_EditRoomTooltip')} placement='top'>
                      <IconButton
                        aria-label='edit room'
                        sx={{ '&:hover': { cursor: 'pointer' } }}
                        onClick={() => { onEditRoomClick(room.id); }}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {showSpinner && (
          <Box sx={{ display: 'flex', justifyContent: 'center', pt: 3 }}>
            <CircularProgress disableShrink />
          </Box>
        )}
      </Box>

      <RoomsModal
        {...modalState}
        onClose={closeModal}
        onAddRoom={onAddRoom}
        onEditRoom={onEditRoom}
        deleteRoom={deleteRoom} />
    </div>
  );
};

export default RoomsPage;
