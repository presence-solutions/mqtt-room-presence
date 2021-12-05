import Typography from '@mui/material/Typography';

type Props = {
  children: React.ReactNode
};

export default function PageTitle({ children }: Props) {
  return (
    <Typography variant='h4' component='h2' align='center' sx={{ mt: { md: 1 } }}>
      {children}
    </Typography>
  );
}
