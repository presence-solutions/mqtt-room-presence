import { useFormatMessage } from '../../intl/helpers';

export default function NotFoundPage() {
  const fm = useFormatMessage();

  return (
    <div>
      {fm('NotFoundPage_Message')}
    </div>
  );
}
