import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';

type Props = {
  open: boolean,
  title: string,
  message: string,
  confirmLabel: string,
  declineLabel: string,
  onConfirm: () => unknown,
  onClose: () => unknown
};

const ConfirmDialog: React.VFC<Props> = ({
  open,
  title,
  message,
  confirmLabel,
  declineLabel,
  onConfirm,
  onClose
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth='xs' fullWidth>
      <DialogTitle sx={{ textAlign: 'center' }}>{title}</DialogTitle>

      <DialogContent sx={{ py: 0 }}>
        {message}
      </DialogContent>

      <DialogActions sx={{ px: 3 }}>
        <Button onClick={onConfirm}>{confirmLabel}</Button>
        <Button onClick={onClose}>{declineLabel}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
