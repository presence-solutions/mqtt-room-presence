export enum ThemeType {
  light = 'light',
  dark = 'dark'
}

export interface GlobalError {
  type: string,
  details: string[]
}
