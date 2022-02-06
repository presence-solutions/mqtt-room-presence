import { configureStore } from '@reduxjs/toolkit';
import throttle from 'lodash/throttle';
import commonReducer from './slices/commonSlice';
import { loadState, saveState } from '../lib/utility/localStorage';

import type { Action, ThunkAction } from '@reduxjs/toolkit';

const preloadedState = loadState();

export const store = configureStore({
  reducer: {
    common: commonReducer
  },
  preloadedState
});

store.subscribe(throttle(() => {
  const state = store.getState();

  saveState({
    common: state.common
  });
}, 1000));

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  Action<string>
>;
