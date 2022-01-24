/**
 * This code is partially copied from official react-intl example
 */

import { useIntl, IntlProvider as ReactIntlProvider } from 'react-intl';
import type { PrimitiveType } from 'intl-messageformat';
// "import type" ensures en messages aren't bundled by default
import type sourceOfTruth from './messages/en.json';

export type LocaleMessages = typeof sourceOfTruth;
export type LocaleKey = keyof LocaleMessages;

export function useFormatMessage(): (
  id: LocaleKey, // only accepts valid keys, not any string
  values?: Record<string, PrimitiveType>
) => string {
  const intl = useIntl();
  return (id, values) => intl.formatMessage({ id }, values);
}

type SupportedLocales = 'en';

export function loadMessages(locale: SupportedLocales): Promise<LocaleMessages> {
  switch (locale) {
    case 'en':
      return import('./messages/en.json');
  }
};

export const IntlProvider: React.FC<
  Omit<React.ComponentProps<typeof ReactIntlProvider>, 'messages'> & {
    messages: LocaleMessages
  }
> = props => <ReactIntlProvider {...props} />;
