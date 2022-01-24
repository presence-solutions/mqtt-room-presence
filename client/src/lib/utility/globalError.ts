import { CombinedError } from 'urql';
import type { GlobalError } from '../../types/common';

const NETWORK_ERROR_TYPE = 'Network Error';
const GRAPHQL_ERROR_TYPE = 'GraphQL Error';

export function parseGlobalError(error: Error): GlobalError {
  let errorType: string = error.name;
  let errorDetails: string[] = [error.message];

  if (error instanceof CombinedError) {
    if (error.networkError) {
      errorType = NETWORK_ERROR_TYPE;
      errorDetails = [error.networkError.message];
    } else if (error.graphQLErrors.length > 0) {
      errorType = GRAPHQL_ERROR_TYPE;
      errorDetails = error.graphQLErrors.map(err => err.message);
    }
  }

  return {
    type: errorType,
    details: errorDetails
  };
}
