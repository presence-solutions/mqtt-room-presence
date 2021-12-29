import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import { red } from '@mui/material/colors';

import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { closeGlobalError } from '../../store/slices/commonSlice';
import { useFormatMessage } from '../../intl/helpers';
import ErrorDetails from '../../components/ErrorDetails/ErrorDetails';

type Props = {};

const GlobalErrorModal: React.VFC<Props> = () => {
  const fm = useFormatMessage();
  const dispatch = useAppDispatch();
  const { open, type, details } = useAppSelector((state) => state.common.globalError);

  const onClose = () => {
    dispatch(closeGlobalError());
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth='sm' fullWidth keepMounted>
      <DialogTitle sx={{ textAlign: 'center', color: red[500] }}>
        {fm('GlobalError_Title')}
      </DialogTitle>

      <DialogContent dividers>
        <ErrorDetails
          typeTitle={fm('Error_Type')}
          detailsTitle={fm('Error_Details')}
          type={type}
          details={details} />
      </DialogContent>

      <DialogActions sx={{ px: 3 }}>
        <Button onClick={onClose}>{fm('Button_Close')}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default GlobalErrorModal;
