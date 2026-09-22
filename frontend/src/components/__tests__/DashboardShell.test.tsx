import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SessionSidebar } from '../SessionSidebar';
import { ChatHeader } from '../ChatHeader';
import { DashboardCards } from '../DashboardCards';
import { useChatStore, makeSession } from '../../store/useChatStore';

describe('Dashboard Shell — layout limpo e minimalista (UI refactor)', () => {
  beforeEach(() => {
    localStorage.clear();
    useChatStore.setState({
      sessions: [makeSession(0)],
      activeIdx: 0,
      isSidebarOpen: true,
      isLoading: false
    });
  });

  it('renderiza a sidebar com logo, navegação adaptada e perfil do usuário', () => {
    render(<SessionSidebar />);

    expect(screen.getByText(/rag político/i)).toBeTruthy();
    expect(screen.getByText(/Novo Chat/i)).toBeTruthy();
    expect(screen.getByText(/Histórico/i)).toBeTruthy();
    expect(screen.getByText(/Base de Conhecimento/i)).toBeTruthy();
    expect(screen.getByText(/Configurações/i)).toBeTruthy();
    expect(screen.getByText('Visitante', { exact: true })).toBeTruthy();
    expect(screen.getByText('visitante@ragpolitico.app', { exact: true })).toBeTruthy();
  });

  it('renderiza o header de saudação com nome e boas-vindas', () => {
    render(<ChatHeader />);

    expect(screen.getByRole('heading', { name: /Olá, Visitante/i })).toBeTruthy();
    expect(screen.getByText(/Boas-vindas à RAG Político/i)).toBeTruthy();
  });

  it('renderiza os cards superiores e a seção de configuração', () => {
    render(<DashboardCards />);

    expect(screen.getByText(/Chats Recentes/i)).toBeTruthy();
    expect(screen.getByText(/Próximos Passos/i)).toBeTruthy();
    expect(screen.getByText(/Terminar a configuração/i)).toBeTruthy();
    expect(screen.getByText(/Fazer upload de documentos/i)).toBeTruthy();
    expect(screen.getByText(/Configurar API Key do LLM/i)).toBeTruthy();
  });
});
