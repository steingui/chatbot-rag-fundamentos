import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyCJNflYVfwWbCxVU9laXB0Iy_wQxDr5qVw",
  authDomain: "rag-eleicoes.firebaseapp.com",
  projectId: "rag-eleicoes",
  storageBucket: "rag-eleicoes.firebasestorage.app",
  messagingSenderId: "1043919586992",
  appId: "1:1043919586992:ios:478ea23f735552cbd11d75"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();

export const auth = getAuth(app);

export default app;

