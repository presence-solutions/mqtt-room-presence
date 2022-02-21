import Typography from '@mui/material/Typography';

type Props = {};

const PageTitle: React.FC<Props> = ({ children }) => (
  <Typography variant='h4' component='h2' align='center' sx={{ lineHeight: '48px' }}>
    {children}
  </Typography>
);

export default PageTitle;
