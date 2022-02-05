/**
 * Custom MUI Switch
 */
import { styled, darken, lighten } from '@mui/material/styles';
import { blue, grey } from '@mui/material/colors';
import Switch from '@mui/material/Switch';

import { ThemeType } from '../../types/common';
import sunIcon from '../../assets/svg/sun.svg';
import moonIcon from '../../assets/svg/moon.svg';

const trackLightColor = grey[200];
const trackDarkColor = grey[500];

const thumbLightColor = darken(blue[700], 0.10);
const thumbDarkColor = lighten(grey[900], 0.15);

const ThemeSwitch = styled(Switch)(({ theme }) => ({
  width: 62,
  height: 34,
  padding: 7,
  '& .MuiSwitch-switchBase': {
    margin: 1,
    padding: 0,
    left: 6,
    '&.Mui-checked': {
      color: '#fff',
      transform: 'translateX(16px)',
      '& .MuiSwitch-thumb:before': {
        backgroundImage: `url(${encodeURIComponent(moonIcon)})`
      },
      '& + .MuiSwitch-track': {
        backgroundColor: trackDarkColor
      }
    }
  },
  '& .MuiSwitch-thumb': {
    backgroundColor: theme.palette.mode === ThemeType.dark ? thumbDarkColor : thumbLightColor,
    width: 32,
    height: 32,
    boxShadow: 'none',
    '&:before': {
      content: '\'\'',
      position: 'absolute',
      width: '100%',
      height: '100%',
      left: 0,
      top: 0,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'center',
      backgroundImage: `url(${encodeURIComponent(sunIcon)})`
    }
  },
  '& .MuiSwitch-track': {
    opacity: 1,
    backgroundColor: trackLightColor,
    borderRadius: 10
  }
}));

export default ThemeSwitch;
