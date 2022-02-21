import { useFormatMessage } from '../../intl/helpers';

type Props = {};

const NotFoundPage: React.VFC<Props> = () => {
  const fm = useFormatMessage();

  return (
    <div>
      {fm('NotFoundPage_Message')}
    </div>
  );
};

export default NotFoundPage;
