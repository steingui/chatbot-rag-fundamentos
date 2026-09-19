import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, onAuthStateChanged, signInAnonymously, type User } from 'firebase/auth';

const appId = import.meta.env.VITE_FIREBASE_APP_ID as string | undefined;

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyCJNflYVfwWbCxVU9laXB0Iy_wQxDr5qVw',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'rag-eleicoes.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'rag-eleicoes',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'rag-eleicoes.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '1043919586992',
  ...(appId ? { appId } : {})
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
const auth = getAuth(app);

let idTokenPromise: Promise<string | null> | null = null;

const signIn = (): Promise<string | null> => {
  if (idTokenPromise) return idTokenPromise;

  idTokenPromise = new Promise<string | null>((resolve) => {
    const current = auth.currentUser;
    if (current) {
      resolve(current.getIdToken().catch(() => null));
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (user: User | null) => {
      if (!user) return;
      unsubscribe();
      resolve(user.getIdToken().catch(() => null));
    });

    signInAnonymously(auth).catch(() => {
      unsubscribe();
      idTokenPromise = null;
      resolve(null);
    });
  });

  return idTokenPromise;
};

export const getIdToken = (): Promise<string | null> => signIn();
