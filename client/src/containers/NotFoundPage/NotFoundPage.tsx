import { useFormatMessage } from '../../intl/helpers';

export default function NotFoundPage() {
  const formatMessage = useFormatMessage();

  return (
    <div>
      {formatMessage('NotFoundPage_Message')}
    </div>
  );
}
