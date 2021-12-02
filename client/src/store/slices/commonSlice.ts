import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ThemeType } from '../../types/common';

interface CommonState {
  theme: ThemeType
}

const initialState: CommonState = {
  theme: ThemeType.light
};

export const commonSlice = createSlice({
  name: 'common',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeType>) => {
      state.theme = action.payload;
    }
  }
});

export const { setTheme } = commonSlice.actions;

export default commonSlice.reducer;
