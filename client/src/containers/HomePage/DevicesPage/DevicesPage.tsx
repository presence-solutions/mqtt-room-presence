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
import { parseGlobalError } from '../../../lib/parsers/globalError';
import { sortArrayByStringId } from '../../../lib/sorters/common';
import PageTitle from '../../../components/PageTitle/PageTitle';
import DevicesModal from './DevicesModal';

type DevicesModalState = {
  open: boolean,
  mode: 'add' | 'edit',
  deviceId: string | null,
  initialValues: {
    deviceName: string,
    deviceUuid: string
  }
};

type Props = {};

const defaultModalState: DevicesModalState = {
  open: false,
  mode: 'add',
  deviceId: null,
  initialValues: {
    deviceName: '',
    deviceUuid: ''
  }
};

const DevicesPage: React.VFC<Props> = () => {
  const dispatch = useAppDispatch();
  const fm = useFormatMessage();

  const [modalState, setModalState] = useState<DevicesModalState>({ ...defaultModalState });

  const [devicesResult] = useGetAllDevicesQuery();
  const [addDeviceResult, addDevice] = useAddDeviceMutation();
  const [updateDeviceResult, updateDevice] = useUpdateDeviceMutation();
  const [removeDeviceResult, removeDevice] = useRemoveDeviceMutation();

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
          deviceName: device.name || '',
          deviceUuid: device.uuid || ''
        }
      });
    }
  };

  const onAddDevice = (name: string, uuid: string) => {
    addDevice({
      newDevice: {
        name,
        uuid
      }
    }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      };
    });
  };

  const onEditDevice = (id: string, name: string, uuid: string) => {
    const device = devices.find(d => d.id === id);

    if (device) {
      updateDevice({
        device: {
          id,
          name,
          uuid
        }
      }).then((result) => {
        closeModal();

        if (result.error) {
          showGlobalError(result.error);
        };
      });
    }
  };

  const deleteDevice = (id: string) => {
    removeDevice({
      deviceId: id
    }).then((result) => {
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
                <TableCell>{fm('DevicesPage_IdColumn')}</TableCell>
                <TableCell>{fm('DevicesPage_NameColumn')}</TableCell>
                <TableCell>{fm('DevicesPage_UuidColumn')}</TableCell>
                <TableCell align='center' sx={{ p: 0 }}>
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
                  <TableCell>{device.id}</TableCell>
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
