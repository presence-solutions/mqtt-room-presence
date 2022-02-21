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
  useGetAllScannersQuery,
  useAddScannerMutation,
  useUpdateScannerMutation,
  useRemoveScannerMutation
} from '../../../generated/graphql';
import { useAppDispatch } from '../../../store/hooks';
import { setGlobalError } from '../../../store/slices/commonSlice';
import { parseGlobalError } from '../../../lib/utility/globalError';
import { sortArrayByIdAndUuid } from '../../../lib/utility/sortArray';
import { TYPE_SCANNER } from '../../../lib/constants/graphql';
import PageTitle from '../../../components/PageTitle/PageTitle';
import ScannersModal from './ScannersModal';

import type { NewScannerInput, UpdateScannerInput } from '../../../generated/graphql';

export type ScannersModalInitialValues = {
  uuid: string
};

type ScannersModalState = {
  open: boolean,
  mode: 'add' | 'edit',
  scannerId: string | null,
  initialValues: ScannersModalInitialValues
};

type Props = {};

const defaultModalState: ScannersModalState = {
  open: false,
  mode: 'add',
  scannerId: null,
  initialValues: {
    uuid: ''
  }
};

const sideColumnWidth = '64px';

const ScannersPage: React.VFC<Props> = () => {
  const dispatch = useAppDispatch();
  const fm = useFormatMessage();

  const [modalState, setModalState] = useState<ScannersModalState>({ ...defaultModalState });

  // Use additional typenames to fix empty lists not updating after first mutation
  const context = useMemo(() => ({ additionalTypenames: [TYPE_SCANNER] }), []);
  const [scannersResult] = useGetAllScannersQuery({ context });

  const [, addScanner] = useAddScannerMutation();
  const [, updateScanner] = useUpdateScannerMutation();
  const [, removeScanner] = useRemoveScannerMutation();

  const scanners = useMemo(() => {
    return scannersResult.data ? sortArrayByIdAndUuid(scannersResult.data.allScanners) : [];
  }, [scannersResult.data]);

  const showSpinner = scannersResult.fetching && scanners.length === 0;

  const showGlobalError = (e: Error) => {
    dispatch(setGlobalError(parseGlobalError(e)));
  };

  useEffect(() => {
    if (scannersResult.error) {
      showGlobalError(scannersResult.error);
    }
  });

  const onAddScannerClick = () => {
    setModalState({
      ...defaultModalState,
      open: true
    });
  };

  const onEditScannerClick = (scannerId: string) => {
    const scanner = scanners.find(s => s.id === scannerId);

    if (scanner) {
      setModalState({
        open: true,
        mode: 'edit',
        scannerId,
        initialValues: {
          uuid: scanner.uuid
        }
      });
    }
  };

  const onAddScanner = (newScanner: NewScannerInput) => {
    addScanner({ newScanner }).then((result) => {
      closeModal();

      if (result.error) {
        showGlobalError(result.error);
      }
    });
  };

  const onEditScanner = (scanner: UpdateScannerInput) => {
    const oldScanner = scanners.find(s => s.id === scanner.id);

    if (oldScanner) {
      scanner.usedInRooms = oldScanner.usedInRooms?.map(room => room.id);

      updateScanner({ scanner }).then((result) => {
        closeModal();

        if (result.error) {
          showGlobalError(result.error);
        }
      });
    }
  };

  const deleteScanner = (scannerId: string) => {
    removeScanner({ scannerId }).then((result) => {
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
      <PageTitle>{fm('ScannersPage_Title')}</PageTitle>

      <Box sx={{ px: { md: 8 }, mt: 2 }}>
        <TableContainer component={Paper}>
          <Table aria-label='scanners list' sx={{ borderCollapse: 'separate' }}>
            <TableHead>
              <TableRow>
                <TableCell align='center' sx={{ width: sideColumnWidth }}>
                  {fm('ScannersPage_IdColumn')}
                </TableCell>
                <TableCell>{fm('ScannersPage_UuidColumn')}</TableCell>
                <TableCell align='center' sx={{ p: 0, width: sideColumnWidth }}>
                  <Tooltip title={fm('ScannersPage_AddScannerTooltip')} placement='top'>
                    <IconButton
                      aria-label='add scanner'
                      sx={{ '&:hover': { cursor: 'pointer' } }}
                      onClick={onAddScannerClick}>
                      <AddIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {scanners.map((scanner, idx) => (
                <TableRow key={idx} hover>
                  <TableCell align='center'>{scanner.id || ''}</TableCell>
                  <TableCell>{scanner.uuid}</TableCell>
                  <TableCell align='center' sx={{ p: 0 }}>
                    {scanner.id && (
                      <Tooltip title={fm('ScannersPage_EditScannerTooltip')} placement='top'>
                        <IconButton
                          aria-label='edit scanner'
                          sx={{ '&:hover': { cursor: 'pointer' } }}
                          onClick={() => { onEditScannerClick(scanner.id!); }}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                    )}
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

      <ScannersModal
        {...modalState}
        onClose={closeModal}
        onAddScanner={onAddScanner}
        onEditScanner={onEditScanner}
        deleteScanner={deleteScanner} />
    </div>
  );
};

export default ScannersPage;
