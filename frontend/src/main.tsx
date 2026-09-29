import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { NextStepProvider, NextStep } from 'nextstepjs';
import './index.css'

import { createTheme, CssBaseline, ThemeProvider } from '@mui/material';
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    mode: 'light',
  },
  typography: {
    fontFamily: [
      '"Montserrat"',
      'system-ui',
      '"Segoe UI"',
      'Roboto',
      'sans-serif'
    ].join(','),
  },
});

import Login from './Login'
import Consent from './Consent'
import SampleWrapper from './Sample'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Login />
  },
  {
    path: '/consent',
    element: <Consent />
  },
  {
    path: '/sample',
    element: <SampleWrapper />
  }
])

import { steps } from './tours';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <NextStepProvider>
        <NextStep steps={steps}>
          <CssBaseline />
          <RouterProvider router={router} />
        </NextStep>
      </NextStepProvider>
    </ThemeProvider>
  </StrictMode>,
)
