import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';

type Props = {
  typeTitle: string,
  detailsTitle: string,
  type: string,
  details: string[]
};

const ErrorsUL = styled('ul')({
  margin: 0
});

const ErrorDetails: React.VFC<Props> = ({ typeTitle, detailsTitle, type, details }) => {
  return (
    <>
      <Typography variant='subtitle1' component='div' sx={{ fontWeight: 700 }} gutterBottom>
        {typeTitle}
      </Typography>

      <Typography variant='body1' component='div' gutterBottom>
        {type}
      </Typography>

      <Typography variant='subtitle1' component='div' sx={{ fontWeight: 700 }} gutterBottom>
        {detailsTitle}
      </Typography>

      <Typography variant='body1' component='div' gutterBottom>
        <ErrorsUL>
          {details.map((detail, idx) => <li key={idx}>{detail}</li>)}
        </ErrorsUL>
      </Typography>
    </>
  );
};

export default ErrorDetails;
