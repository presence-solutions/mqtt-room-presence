import { useState, useEffect } from 'react';
import { useFormik } from 'formik';
import * as yup from 'yup';

import Box from '@mui/material/Box';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import DeleteIcon from '@mui/icons-material/Delete';

import { useFormatMessage } from '../../../intl/helpers';
import ConfirmDialog from '../../../components/ConfirmDialog/ConfirmDialog';

import type { NewDeviceInput, UpdateDeviceInput } from '../../../generated/graphql';
import type { DevicesModalInitialValues } from './DevicesPage';

type Props = {
  open: boolean,
  mode: 'add' | 'edit',
  deviceId: string | null,
  initialValues: DevicesModalInitialValues,
  onClose: () => void,
  onAddDevice: (newDevice: NewDeviceInput) => void,
  onEditDevice: (device: UpdateDeviceInput) => void,
  deleteDevice: (deviceId: string) => void
};

const DevicesModal: React.VFC<Props> = ({
  open,
  mode,
  deviceId,
  initialValues,
  onClose,
  onAddDevice,
  onEditDevice,
  deleteDevice
}: Props) => {
  const fm = useFormatMessage();

  const [loading, setLoading] = useState(false);
  const [openDeleteConfirmDialog, setOpenDeleteConfirmDialog] = useState(false);

  const title = mode === 'add' ? fm('DevicesModal_AddTitle') : fm('DevicesModal_EditTitle');
  const submitButtonText = mode === 'add' ? fm('Button_Add') : fm('Button_Save');

  const validationSchema = yup.object({
    name: yup.string().required(fm('Validation_Required')),
    uuid: yup.string().required(fm('Validation_Required'))
  });

  const formik = useFormik({
    enableReinitialize: true,
    initialValues,
    validationSchema,
    onSubmit: (values) => {
      setLoading(true);

      if (mode === 'add') {
        onAddDevice({ ...values });
      } else if (deviceId !== null) {
        onEditDevice({
          id: deviceId,
          ...values
        });
      }
    }
  });

  // Reset form is needed when edit same item or add a new one multiple times
  useEffect(() => {
    if (open) {
      formik.resetForm();
      setLoading(false);
    }
  }, [open]);

  const onDeleteDeviceClick = () => {
    setOpenDeleteConfirmDialog(true);
  };

  const onDeleteConfirmDialogClose = () => {
    setOpenDeleteConfirmDialog(false);
  };

  const onDeleteConfirm = () => {
    onDeleteConfirmDialogClose();

    if (deviceId) {
      setLoading(true);
      deleteDevice(deviceId);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth keepMounted>
        <form onSubmit={formik.handleSubmit}>
          <DialogTitle sx={{ textAlign: 'center' }}>{title}</DialogTitle>

          <DialogContent sx={{ py: 0 }}>
            <Box sx={{ py: 1 }}>
              <TextField
                name='name'
                type='text'
                label={fm('DevicesModal_NameFieldLabel')}
                placeholder={fm('DevicesModal_NameFieldPlaceholder')}
                value={formik.values.name}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
                onChange={formik.handleChange}
                variant='outlined'
                fullWidth
                autoFocus />

              <TextField
                sx={{ mt: 2 }}
                name='uuid'
                type='text'
                label={fm('DevicesModal_UuidFieldLabel')}
                placeholder={fm('DevicesModal_UuidFieldPlaceholder')}
                value={formik.values.uuid}
                error={formik.touched.uuid && Boolean(formik.errors.uuid)}
                helperText={formik.touched.uuid && formik.errors.uuid}
                onChange={formik.handleChange}
                variant='outlined'
                fullWidth
                autoFocus />
            </Box>
          </DialogContent>

          <DialogActions sx={{ px: 3 }}>
            {mode === 'edit' && deviceId !== null && (
              <IconButton
                sx={{ mr: 'auto' }}
                disabled={loading}
                onClick={onDeleteDeviceClick}>
                <DeleteIcon />
              </IconButton>
            )}
            <Button type='submit' disabled={loading}>{submitButtonText}</Button>
            <Button onClick={onClose} disabled={loading}>{fm('Button_Cancel')}</Button>
          </DialogActions>
        </form>
      </Dialog>

      <ConfirmDialog
        open={openDeleteConfirmDialog}
        title={fm('DevicesDeleteConfirm_Title')}
        message={fm('DevicesDeleteConfirm_Message')}
        confirmLabel={fm('Button_Delete')}
        declineLabel={fm('Button_Cancel')}
        onConfirm={onDeleteConfirm}
        onClose={onDeleteConfirmDialogClose} />
    </>
  );
};

export default DevicesModal;
