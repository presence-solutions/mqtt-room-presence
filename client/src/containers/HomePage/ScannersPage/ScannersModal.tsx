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

import type { NewScannerInput, UpdateScannerInput } from '../../../generated/graphql';
import type { ScannersModalInitialValues } from './ScannersPage';

type Props = {
  open: boolean,
  mode: 'add' | 'edit',
  scannerId: string | null,
  initialValues: ScannersModalInitialValues,
  onClose: () => void,
  onAddScanner: (newScanner: NewScannerInput) => void,
  onEditScanner: (scanner: UpdateScannerInput) => void,
  deleteScanner: (scannerId: string) => void
};

const ScannersModal: React.VFC<Props> = ({
  open,
  mode,
  scannerId,
  initialValues,
  onClose,
  onAddScanner,
  onEditScanner,
  deleteScanner
}: Props) => {
  const fm = useFormatMessage();

  const [loading, setLoading] = useState(false);
  const [openDeleteConfirmDialog, setOpenDeleteConfirmDialog] = useState(false);

  const title = mode === 'add' ? fm('ScannersModal_AddTitle') : fm('ScannersModal_EditTitle');
  const submitButtonText = mode === 'add' ? fm('Button_Add') : fm('Button_Save');

  const validationSchema = yup.object({
    uuid: yup.string().required(fm('Validation_Required'))
  });

  const formik = useFormik({
    enableReinitialize: true,
    initialValues,
    validationSchema,
    onSubmit: (values) => {
      setLoading(true);

      if (mode === 'add') {
        onAddScanner({ ...values });
      } else if (scannerId !== null) {
        onEditScanner({
          id: scannerId,
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

  const onDeleteScannerClick = () => {
    setOpenDeleteConfirmDialog(true);
  };

  const onDeleteConfirmDialogClose = () => {
    setOpenDeleteConfirmDialog(false);
  };

  const onDeleteConfirm = () => {
    onDeleteConfirmDialogClose();

    if (scannerId) {
      setLoading(true);
      deleteScanner(scannerId);
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth keepMounted>
        <form onSubmit={formik.handleSubmit}>
          <DialogTitle sx={{ textAlign: 'center', pb: 1 }}>{title}</DialogTitle>

          <DialogContent sx={{ py: 0 }}>
            <Box sx={{ py: 1 }}>
              <TextField
                name='uuid'
                type='text'
                label={fm('ScannersModal_UuidFieldLabel')}
                placeholder={fm('ScannersModal_UuidFieldPlaceholder')}
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
            {mode === 'edit' && scannerId !== null && (
              <IconButton
                sx={{ mr: 'auto' }}
                disabled={loading}
                onClick={onDeleteScannerClick}>
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
        title={fm('ScannersDeleteConfirm_Title')}
        message={fm('ScannersDeleteConfirm_Message')}
        confirmLabel={fm('Button_Delete')}
        declineLabel={fm('Button_Cancel')}
        onConfirm={onDeleteConfirm}
        onClose={onDeleteConfirmDialogClose} />
    </>
  );
};

export default ScannersModal;
