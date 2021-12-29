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

type Props = {
  open: boolean,
  mode: 'add' | 'edit',
  roomId: string | null,
  initialValues: {
    roomName: string
  },
  onClose: () => void,
  onAddRoom: (name: string) => void,
  onEditRoom: (id: string, name: string) => void,
  deleteRoom: (id: string) => void
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

  const title = mode === 'add' ? fm('RoomsModal_AddTitle') : fm('RoomsModal_EditTitle');
  const submitButtonText = mode === 'add' ? fm('Button_Add') : fm('Button_Save');

  const validationSchema = yup.object({
    roomName: yup.string().required(fm('Validation_Required'))
  });

  const formik = useFormik({
    enableReinitialize: true,
    initialValues,
    validationSchema,
    onSubmit: (values) => {
      setLoading(true);

      if (mode === 'add') {
        onAddRoom(values.roomName);
      } else if (roomId !== null) {
        onEditRoom(roomId, values.roomName);
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

  const onDeleteRoomClick = (roomId: string) => {
    setLoading(true);
    deleteRoom(roomId);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth keepMounted>
      <form onSubmit={formik.handleSubmit}>
        <DialogTitle sx={{ textAlign: 'center' }}>{title}</DialogTitle>

        <DialogContent sx={{ py: 0 }}>
          <Box sx={{ py: 1 }}>
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

        <DialogActions sx={{ px: 3 }}>
          {mode === 'edit' && roomId !== null && (
            <IconButton
              sx={{ mr: 'auto' }}
              disabled={loading}
              onClick={() => { onDeleteRoomClick(roomId); }}>
              <DeleteIcon />
            </IconButton>
          )}
          <Button type='submit' disabled={loading}>{submitButtonText}</Button>
          <Button onClick={onClose} disabled={loading}>{fm('Button_Cancel')}</Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default RoomsModal;
