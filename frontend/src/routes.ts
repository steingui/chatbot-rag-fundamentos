import type { ComponentType } from 'react';
import App from './App';
import { PrivacyPage } from './pages/PrivacyPage';

export interface Route {
  type: ComponentType;
}

export function resolveRoute(pathname: string): Route {
  if (pathname.startsWith('/privacidade')) {
    return { type: PrivacyPage };
  }
  return { type: App };
}
