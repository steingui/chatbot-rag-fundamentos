const EMAIL = 'contato@politichat.com.br';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-extrabold tracking-tight text-neutral-950">{title}</h2>
      <div className="space-y-2 text-sm leading-relaxed text-neutral-700">{children}</div>
    </section>
  );
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1.5 pl-5">
      {items.map((item) => (
        <li key={item} className="list-disc marker:text-emerald-500">
          {item}
        </li>
      ))}
    </ul>
  );
}

export function PrivacyPage() {
  return (
    <main className="min-h-screen w-screen overflow-y-auto bg-[#F2F2F7]">
      <div className="mx-auto max-w-3xl px-5 py-10 sm:px-8 sm:py-14">
        <a
          href="/"
          className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700 hover:text-emerald-900 apple-spring"
        >
          ← Voltar ao chat
        </a>

        <div className="mt-6 apple-glass rounded-3xl p-6 sm:p-10 space-y-10">
          <header className="space-y-3 border-b border-black/5 pb-8">
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-neutral-950">
              Política de Privacidade
            </h1>
            <p className="text-sm text-neutral-500">
              Última atualização: 1 de janeiro de 2025 · Aplicável ao domínio{' '}
              <span className="font-semibold text-neutral-700">politichat.com.br</span>
            </p>
          </header>

          <Section title="1. Quem somos">
            <p>
              O <strong>PolitiChat</strong> é um assistente de informação política que responde
              perguntas sobre PECs, projetos de lei, votações, TSE e checagens de fatos com base em
              fontes públicas. Esta página descreve como tratamos seus dados pessoais em
              conformidade com a <strong>Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018)</strong>.
            </p>
          </Section>

          <Section title="2. Dados que coletamos">
            <List
              items={[
                'Identificadores de conta fornecidos por provedores de login (Google/Apple) ou acesso anônimo.',
                'Histórico de conversas e perguntas enviadas ao assistente.',
                'Dados técnicos de uso, como navegador, dispositivo e páginas acessadas.',
              ]}
            />
          </Section>

          <Section title="3. Finalidades do tratamento">
            <List
              items={[
                'Fornecer e melhorar as respostas do assistente.',
                'Garantir a segurança e prevenir abusos na plataforma.',
                'Cumprir obrigações legais e regulatórias aplicáveis.',
              ]}
            />
          </Section>

          <Section title="4. Compartilhamento de dados">
            <p>
              Não vendemos dados pessoais. Podemos compartilhar dados apenas com provedores de
              infraestrutura e processamento (nuvem, banco de dados vetorial e LLMs) estritamente
              necessários à operação do serviço, sempre mediante obrigações de confidencialidade.
            </p>
          </Section>

          <Section title="5. Seus direitos (LGPD)">
            <List
              items={[
                'Confirmar a existência de tratamento e acessar seus dados.',
                'Corrigir dados incompletos, inexatos ou desatualizados.',
                'Solicitar anonimização, bloqueio ou eliminação de dados desnecessários.',
                'Revogar consentimento e solicitar a exclusão completa da conta e dos dados pessoais.',
                'Reclamar perante a Autoridade Nacional de Proteção de Dados (ANPD).',
              ]}
            />
          </Section>

          <Section title="6. Retenção e exclusão">
            <p>
              Os dados são mantidos apenas pelo tempo necessário às finalidades descritas. A
              exclusão da conta remove o histórico de conversas e os dados pessoais associados,
              conforme previsto nos Termos de Uso abaixo.
            </p>
          </Section>

          <Section title="7. Cookies e armazenamento local">
            <p>
              Utilizamos armazenamento local do navegador para manter sua sessão e preferências.
              Não utilizamos cookies de rastreamento de terceiros para publicidade.
            </p>
          </Section>

          <Section title="8. Contato — Encarregado (DPO)">
            <p>
              Para exercer seus direitos ou esclarecer dúvidas sobre privacidade, envie e-mail para{' '}
              <a href={`mailto:${EMAIL}`} className="font-bold text-emerald-700 hover:underline">
                {EMAIL}
              </a>
              .
            </p>
          </Section>

          <header className="space-y-3 border-t border-black/5 pt-10">
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-neutral-950">
              Termos de Uso
            </h2>
            <p className="text-sm text-neutral-500">
              Última atualização: 1 de janeiro de 2025
            </p>
          </header>

          <Section title="1. Aceitação">
            <p>
              Ao utilizar o PolitiChat, você concorda com estes Termos de Uso e com a Política de
              Privacidade. Caso não concorde, não utilize o serviço.
            </p>
          </Section>

          <Section title="2. Natureza do serviço">
            <p>
              O PolitiChat é uma ferramenta de apoio à informação baseada em fontes públicas e em
              modelos de linguagem. As respostas têm caráter informativo e não substituem opinião
              jurídica, profissional ou a consulta a fontes oficiais.
            </p>
          </Section>

          <Section title="3. Uso aceitável">
            <List
              items={[
                'É vedado o uso para fins ilícitos, fraudulentos ou que violem direitos de terceiros.',
                'É vedado tentar contornar limitações, extrair dados em massa ou sobrecarregar a plataforma.',
                'O usuário é responsável pelas informações que envia e pelo uso que faz das respostas.',
              ]}
            />
          </Section>

          <Section title="4. Propriedade intelectual">
            <p>
              O conteúdo das fontes públicas pertence aos seus respectivos titulares. O PolitiChat
              não reivindica titularidade sobre textos legislativos ou decisões públicas utilizados
              nas respostas.
            </p>
          </Section>

          <Section title="5. Exclusão de conta e dados">
            <p>
              Você pode solicitar a exclusão da conta e dos dados pessoais a qualquer momento pelo
              e-mail {EMAIL}. Após a solicitação, os dados são removidos em prazo compatível com a
              LGPD, ressalvadas obrigações legais de retenção.
            </p>
          </Section>

          <Section title="6. Limitação de responsabilidade">
            <p>
              O serviço é fornecido "como está". Não garantimos disponibilidade ininterrupta nem a
              exatidão absoluta das respostas geradas automaticamente, dentro dos limites permitidos
              pela legislação aplicável.
            </p>
          </Section>

          <Section title="7. Alterações">
            <p>
              Podemos atualizar estes Termos e a Política de Privacidade a qualquer momento. A
              versão vigente será sempre publicada nesta página.
            </p>
          </Section>

          <Section title="8. Legislação aplicável">
            <p>
              Estes Termos são regidos pela legislação brasileira, em especial a LGPD e o Marco
              Civil da Internet (Lei nº 12.965/2014), com foro na comarca do domicílio do usuário.
            </p>
          </Section>
        </div>

        <footer className="mt-8 pb-10 text-center text-xs text-neutral-500">
          © 2025 PolitiChat · politichat.com.br
        </footer>
      </div>
    </main>
  );
}
