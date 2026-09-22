import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SessionSidebar } from '../SessionSidebar';
import { ChatHeader } from '../ChatHeader';
import { DashboardCards } from '../DashboardCards';
import { useChatStore, makeSession, SUMMARY_PROMPT } from '../../store/useChatStore';

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

  it('renderiza as ações de contexto na sidebar', () => {
    render(<SessionSidebar />);

    expect(screen.getByText(/Resumir chat/i)).toBeTruthy();
    expect(screen.getByText(/Limpar contexto/i)).toBeTruthy();
    expect(screen.getByText(/Limpar tudo/i)).toBeTruthy();
  });

  it('desabilita as ações de contexto quando não há histórico do usuário', () => {
    render(<SessionSidebar />);

    expect((screen.getByText(/Resumir chat/i).closest('button') as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByText(/Limpar contexto/i).closest('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('Resumir chat envia o prompt canônico de resumo via stream', () => {
    const sendMessageStream = vi.fn().mockResolvedValue(undefined);
    const session = makeSession(0);
    session.messages.push({
      id: 'u1',
      role: 'user',
      content: 'Quais emendas foram pagas?',
      timestamp: new Date()
    });
    useChatStore.setState({ sessions: [session], activeIdx: 0, sendMessageStream });

    render(<SessionSidebar />);
    fireEvent.click(screen.getByText(/Resumir chat/i));

    expect(sendMessageStream).toHaveBeenCalledWith(SUMMARY_PROMPT);
  });

  it('Limpar contexto reinicia a sessão ativa mantendo a sessão viva', () => {
    const session = makeSession(0);
    session.messages.push({
      id: 'u1',
      role: 'user',
      content: 'Quais emendas foram pagas?',
      timestamp: new Date()
    });
    useChatStore.setState({ sessions: [session], activeIdx: 0 });

    render(<SessionSidebar />);
    fireEvent.click(screen.getByText(/Limpar contexto/i));

    const { sessions } = useChatStore.getState();
    expect(sessions).toHaveLength(1);
    expect(sessions[0].messages.some(m => m.role === 'user')).toBe(false);
    expect(sessions[0].messages[0].content).toMatch(/reiniciada/i);
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
