import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { resolveRoute } from './routes.ts'

const { type: Page } = resolveRoute(window.location.pathname)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)
