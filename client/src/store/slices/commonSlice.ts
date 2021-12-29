import { createSlice } from '@reduxjs/toolkit';
import { ThemeType } from '../../types/common';

import type { PayloadAction } from '@reduxjs/toolkit';
import type { GlobalError } from '../../types/common';

interface GlobalErrorState extends GlobalError {
  open: boolean
};

type CommonState = {
  theme: ThemeType,
  globalError: GlobalErrorState
};

const initialState: CommonState = {
  theme: ThemeType.light,
  globalError: {
    open: false,
    type: '',
    details: []
  }
};

export const commonSlice = createSlice({
  name: 'common',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeType>) => {
      state.theme = action.payload;
    },
    setGlobalError: (state, action: PayloadAction<GlobalError>) => {
      state.globalError = {
        open: true,
        ...action.payload
      };
    },
    closeGlobalError: (state, action: PayloadAction<void>) => {
      state.globalError.open = false;
    }
  }
});

export const { setTheme, setGlobalError, closeGlobalError } = commonSlice.actions;

export default commonSlice.reducer;
