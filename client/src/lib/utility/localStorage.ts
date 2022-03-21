import type { RootState } from '../../store/store';

const REDUX_STATE_KEY = 'STATE';

export function saveState(state: Partial<RootState>): void {
  try {
    const serializedState = JSON.stringify(state);
    localStorage.setItem(REDUX_STATE_KEY, serializedState);
  } catch (e: any) { }
}

export function loadState(): any {
  try {
    const serializedState = localStorage.getItem(REDUX_STATE_KEY);

    if (serializedState) {
      return JSON.parse(serializedState);
    }

    return undefined;
  } catch (e: any) {
    return undefined;
  }
}
