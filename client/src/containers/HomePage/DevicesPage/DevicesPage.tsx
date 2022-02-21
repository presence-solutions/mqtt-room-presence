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
  useGetAllDevicesQuery,
  useAddDeviceMutation,
  useUpdateDeviceMutation,
  useRemoveDeviceMutation
} from '../../../generated/graphql';
import { useAppDispatch } from '../../../store/hooks';
import { setGlobalError } from '../../../store/slices/commonSlice';
import { parseGlobalError } from '../../../lib/utility/globalError';
import { sortArrayByStringId } from '../../../lib/utility/sortArray';
import { TYPE_DEVICE } from '../../../lib/constants/graphql';
import PageTitle from '../../../components/PageTitle/PageTitle';
import DevicesModal from './DevicesModal';

import type { NewDeviceInput, UpdateDeviceInput } from '../../../generated/graphql';

export type DevicesModalInitialValues = {
  name: string,
  uuid: string
};

type DevicesModalState = {
  open: boolean,
  mode: 'add' | 'edit',
  deviceId: string | null,
  initialValues: DevicesModalInitialValues
};

type Props = {};

const defaultModalState: DevicesModalState = {
  open: false,
  mode: 'add',
  deviceId: null,
  initialValues: {
    name: '',
    uuid: ''
  }
};

const sideColumnWidth = '64px';

const DevicesPage: React.VFC<Props> = () => {
  const dispatch = useAppDispatch();
  const fm = useFormatMessage();

  const [modalState, setModalState] = useState<DevicesModalState>({ ...defaultModalState });

  // Use additional typenames to fix empty lists not updating after first mutation
  const context = useMemo(() => ({ additionalTypenames: [TYPE_DEVICE] }), []);
  const [devicesResult] = useGetAllDevicesQuery({ context });

  const [, addDevice] = useAddDeviceMutation();
  const [, updateDevice] = useUpdateDeviceMutation();
  const [, removeDevice] = useRemoveDeviceMutation();

  const devices = useMemo(() => {
    return devicesResult.data ? sortArrayByStringId(devicesResult.data.allDevices) : [];
  }, [devicesResult.data]);

  const showSpinner = devicesResult.fetching && devices.length === 0;

  const showGlobalError = (e: Error) => {
    dispatch(setGlobalError(parseGlobalError(e)));
  };

  useEffect(() => {
    if (devicesResult.error) {
      showGlobalError(devicesResult.error);
    }
  });

  const onAddDeviceClick = () => {
    setModalState({
      ...defaultModalState,
      open: true
    });
  };

  const onEditDeviceClick = (deviceId: string) => {
    const device = devices.find(r => r.id === deviceId);

    if (device) {
      setModalState({
        open: true,
        mode: 'edit',
        deviceId,
        initialValues: {
          name: device.name || '',
          uuid: device.uuid || ''
        }
      });
    }
  };

  const onAddDevice = (newDevice: NewDeviceInput) => {
    addDevice({ newDevice }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      }
    });
  };

  const onEditDevice = (device: UpdateDeviceInput) => {
    updateDevice({ device }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      }
    });
  };

  const deleteDevice = (deviceId: string) => {
    removeDevice({ deviceId }).then((result) => {
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
      <PageTitle>{fm('DevicesPage_Title')}</PageTitle>

      <Box sx={{ px: { md: 8 }, mt: 2 }}>
        <TableContainer component={Paper}>
          <Table aria-label='devices list' sx={{ borderCollapse: 'separate' }}>
            <TableHead>
              <TableRow>
                <TableCell align='center' sx={{ width: sideColumnWidth }}>
                  {fm('DevicesPage_IdColumn')}
                </TableCell>
                <TableCell sx={{ width: '35%' }}>{fm('DevicesPage_NameColumn')}</TableCell>
                <TableCell>{fm('DevicesPage_UuidColumn')}</TableCell>
                <TableCell align='center' sx={{ p: 0, width: sideColumnWidth }}>
                  <Tooltip title={fm('DevicesPage_AddDeviceTooltip')} placement='top'>
                    <IconButton
                      aria-label='add device'
                      sx={{ '&:hover': { cursor: 'pointer' } }}
                      onClick={onAddDeviceClick}>
                      <AddIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {devices.map(device => (
                <TableRow key={device.id} hover>
                  <TableCell align='center'>{device.id}</TableCell>
                  <TableCell>{device.name}</TableCell>
                  <TableCell>{device.uuid}</TableCell>
                  <TableCell align='center' sx={{ p: 0 }}>
                    <Tooltip title={fm('DevicesPage_EditDeviceTooltip')} placement='top'>
                      <IconButton
                        aria-label='edit device'
                        sx={{ '&:hover': { cursor: 'pointer' } }}
                        onClick={() => { onEditDeviceClick(device.id); }}>
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

      <DevicesModal
        {...modalState}
        onClose={closeModal}
        onAddDevice={onAddDevice}
        onEditDevice={onEditDevice}
        deleteDevice={deleteDevice} />
    </div>
  );
};

export default DevicesPage;
