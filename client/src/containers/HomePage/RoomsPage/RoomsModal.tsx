import { useEffect } from 'react';
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

import type { RoomsModalState } from './RoomsPage';
import { useFormatMessage } from '../../../intl/helpers';

interface Props extends RoomsModalState {
  onClose: () => void,
  onAddSubmit: (name: string) => void,
  onEditSubmit: (id: number, name: string) => void,
  deleteHandler: (id: number) => void
}

export default function RoomsModal({
  open,
  mode,
  roomId,
  initialValues,
  onClose,
  onAddSubmit,
  onEditSubmit,
  deleteHandler
}: Props) {
  const fm = useFormatMessage();

  let title: string;
  let submitButtonText: string;

  if (mode === 'add') {
    title = fm('RoomsModal_AddTitle');
    submitButtonText = fm('Button_Add');
  } else {
    title = fm('RoomsModal_EditTitle');
    submitButtonText = fm('Button_Save');
  }

  const validationSchema = yup.object({
    roomName: yup.string().required(fm('Validation_Required'))
  });

  const formik = useFormik({
    enableReinitialize: true,
    initialValues,
    validationSchema,
    onSubmit: (values, { resetForm }) => {
      if (mode === 'add') {
        onAddSubmit(values.roomName);
      } else if (roomId !== null) {
        onEditSubmit(roomId, values.roomName);
      }
    }
  });

  // Reset form is needed when same button clicked twice
  useEffect(() => {
    if (open) {
      formik.resetForm();
    }
  }, [open]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth>
      <form onSubmit={formik.handleSubmit}>
        <DialogTitle sx={{ textAlign: 'center' }}>{title}</DialogTitle>

        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              name='roomName'
              type='text'
              label={fm('RoomsModal_NameFieldLabel')}
              placeholder={fm('RoomsModal_NameFieldPlaceholder')}
              value={formik.values.roomName}
              error={formik.touched.roomName && Boolean(formik.errors.roomName)}
              helperText={formik.touched.roomName && formik.errors.roomName}
              onChange={formik.handleChange}
              variant='outlined'
              fullWidth
              autoFocus />
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 2 }}>
          {mode === 'edit' && roomId !== null &&
            <IconButton sx={{ mr: 'auto' }} onClick={() => { deleteHandler(roomId); }}>
              <DeleteIcon />
            </IconButton>
          }
          <Button type='submit'>{submitButtonText}</Button>
          <Button onClick={onClose}>{fm('Button_Cancel')}</Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
