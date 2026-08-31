import { auth } from './firebase';

const API_BASE_URL = 'http://localhost:10000'; // Em dev local ou Render URL em prod

export interface SourceObject {
  type: string;
  label: string;
  url?: string;
  raw_file: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceObject[];
}

export async function sendChatMessage(query: string, sessionId: string = 'default', model?: string): Promise<ChatResponse> {
  const token = await auth.currentUser?.getIdToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      query,
      session_id: sessionId,
      model: model || undefined,
    }),
  });

  if (!response.ok) {
    throw new Error(`Erro na API (${response.status}): ${response.statusText}`);
  }

  return response.json();
}
