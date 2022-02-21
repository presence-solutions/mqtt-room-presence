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

import type { NewRoomInput, UpdateRoomInput } from '../../../generated/graphql';
import type { RoomsModalInitialValues } from './RoomsPage';

type Props = {
  open: boolean,
  mode: 'add' | 'edit',
  roomId: string | null,
  initialValues: RoomsModalInitialValues,
  onClose: () => void,
  onAddRoom: (newRoom: NewRoomInput) => void,
  onEditRoom: (room: UpdateRoomInput) => void,
  deleteRoom: (roomId: string) => void
};

const RoomsModal: React.VFC<Props> = ({
  open,
  mode,
  roomId,
  initialValues,
  onClose,
  onAddRoom,
  onEditRoom,
  deleteRoom
}: Props) => {
  const fm = useFormatMessage();

  const [loading, setLoading] = useState(false);
  const [openDeleteConfirmDialog, setOpenDeleteConfirmDialog] = useState(false);

  const title = mode === 'add' ? fm('RoomsModal_AddTitle') : fm('RoomsModal_EditTitle');
  const submitButtonText = mode === 'add' ? fm('Button_Add') : fm('Button_Save');

  const validationSchema = yup.object({
    name: yup.string().required(fm('Validation_Required'))
  });

  const formik = useFormik({
    enableReinitialize: true,
    initialValues,
    validationSchema,
    onSubmit: (values) => {
      setLoading(true);

      if (mode === 'add') {
        onAddRoom({ ...values });
      } else if (roomId !== null) {
        onEditRoom({
          id: roomId,
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

  const onDeleteRoomClick = () => {
    setOpenDeleteConfirmDialog(true);
  };

  const onDeleteConfirmDialogClose = () => {
    setOpenDeleteConfirmDialog(false);
  };

  const onDeleteConfirm = () => {
    onDeleteConfirmDialogClose();

    if (roomId) {
      setLoading(true);
      deleteRoom(roomId);
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
                name='name'
                type='text'
                label={fm('RoomsModal_NameFieldLabel')}
                placeholder={fm('RoomsModal_NameFieldPlaceholder')}
                value={formik.values.name}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
                onChange={formik.handleChange}
                variant='outlined'
                fullWidth
                autoFocus />
            </Box>
          </DialogContent>

          <DialogActions sx={{ px: 3 }}>
            {mode === 'edit' && roomId !== null && (
              <IconButton
                sx={{ mr: 'auto' }}
                disabled={loading}
                onClick={onDeleteRoomClick}>
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
        title={fm('RoomsDeleteConfirm_Title')}
        message={fm('RoomsDeleteConfirm_Message')}
        confirmLabel={fm('Button_Delete')}
        declineLabel={fm('Button_Cancel')}
        onConfirm={onDeleteConfirm}
        onClose={onDeleteConfirmDialogClose} />
    </>
  );
};

export default RoomsModal;
