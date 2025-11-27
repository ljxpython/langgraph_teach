import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRouter from './AppRouter'
import './i18n.ts';
import 'katex/dist/katex.min.css';
// eslint-disable  MC8yOmFIVnBZMlhtblk3a3ZiUG1yS002UlRsb2JnPT06OGQ2YTZmOGU=



createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppRouter />
  </StrictMode>
)
// @ts-expect-error  MS8yOmFIVnBZMlhtblk3a3ZiUG1yS002UlRsb2JnPT06OGQ2YTZmOGU=
