# Histórico de reprodução e estatísticas por usuário

Data: 2026-11-19
Pedido: adicione ao prompts.md / Implemente histórico de reprodução e estatísticas por usuário.

## Escopo e decisões
Evolução incremental no Python/Streamlit existente. Histórico por conta, persistido
em history.json no diretório isolado do usuário, usando escrita atômica e lock atuais.
Manter biblioteca, playlists, fila editável e abertura de links externos.
Dados continuam temporários no Community Cloud por decisão anterior da dupla.
Não registrar links abertos em serviços: não há evidência da reprodução nesses serviços.

## Critérios de contagem
- Uma confirmação por tentativa após 5 segundos de reprodução efetiva ou metade da
  duração de faixa com menos de 10 segundos. Duração desconhecida usa 5 segundos.
- O navegador mede avanço de currentTime em relação ao relógio monotônico, ajustado
  por playbackRate, excluindo pausa, busca, buffer e mudanças de fonte.
- Intervalos de amostragem superiores a 2 segundos são descartados conservadoramente.
- Rerun, alteração de filtros/fila, pausa/resume e seek não iniciam outra tentativa.
- Tocar novamente, trocar de faixa, reiniciar por Anterior e ciclos de repetição
  iniciam novas tentativas. Uma nova tentativa só conta após atingir o mínimo novamente.
- Identificador UUID de tentativa é deduplicado no servidor e persiste no histórico.
- Confirmações aguardam acknowledgement, permitindo reenvio sem aumentar a contagem.
- Validar faixa na biblioteca da conta, origem local e duração mínima no servidor.
- Timestamp e snapshots de título/artista/álbum vêm do servidor/biblioteca, não do navegador.
- Não apresentar essa medição como prova de audição humana ou relatório antifraude.

## Histórico e estatísticas
- Nova aba Histórico acessível a usuários autenticados.
- Listar as mais recentes primeiro, com data/hora de São Paulo, 20 registros por página.
- Filtros: Hoje, Últimos 7 dias (hoje e seis dias anteriores), Todo o histórico disponível.
- Armazenar UTC com fuso; calcular períodos por dias no America/Sao_Paulo, sem usar
  o fuso do host. Não incluir datas futuras nos resultados.
- Métricas: reproduções confirmadas e quantidade de músicas distintas no período.
- Ranking por quantidade de reproduções; desempate por título e ID. Não somar duração
  completa das músicas para inventar tempo ouvido. Usar o snapshot mais recente no ranking.
- Tocar novamente e adicionar ao final da fila usando o player existente.
- Biblioteca/arquivo removido mantém o registro histórico, mas desabilita reprodução.
- Limpar exige confirmação explícita, afeta apenas a conta e todo o histórico, independentemente
  do filtro atual. Não alterar biblioteca, playlists ou áudio em execução.
- Limpar gira generation, invalidando confirmações anteriores ainda pendentes em outras abas.
  A tentativa já contada não é automaticamente registrada de novo após limpar.

## Implementação
core/listening_history.py: validação, idempotência, persistência, períodos e ranking.
ui/listening_history.py: tela, métricas, ranking, páginas, reprodução/enfileiramento e limpeza.
ui/browser_player/index.html: medição conservadora de escuta, tentativa e confirmações.
ui/browser_player.py: validação/acknowledgement separado do feedback de transporte.
core/player.py: informar a última ação para distinguir restart de seek/pause/resume.
app.py: rota Histórico. tzdata em requirements para fuso consistente no Windows/Linux.

## Verificação
Testes de limiar, duplicação, concorrência, isolamento, arquivos indisponíveis/corrompidos,
limpeza com confirmação pendente, períodos na virada do dia e ranking.
AppTest: estatísticas, tocar/enfileirar, confirmação de limpeza e integração no app principal.
E2E com áudio real: seeks e tempo pausado não contam; escuta efetiva conta uma vez;
rerun não duplica; replay conta outra tentativa; limpar não reinsere a tentativa já contada.
Reexecutar regressões de fila editável, MP3/WAV/FLAC e biblioteca mista com links.

## Limites
Não há recuperação de dados após reinício do Community Cloud. Medição é conservadora
e depende de eventos do navegador, sem garantia de entrega após fechamento abrupto da aba
antes da confirmação. Arquivos externos não são reproduzidos nem contabilizados pelo app.
Sem commit, push ou deploy solicitados nesta etapa. CLI OpenSpec indisponível conforme
diagnóstico anterior; esta especificação fica em SPEC, mantendo os artefatos existentes.


## Integração assíncrona
O componente de áudio usa fragmento Streamlit. Confirmações em segundo plano não
reexecutam o app inteiro enquanto outra aba está sendo editada. Na aba Histórico,
a confirmação atualiza as métricas. O fragmento restaura a identidade autenticada
armazenada no session_state antes de acessar caminhos por conta, pois um rerun do
fragmento não executa o setup de app.py. Teste específico cobre esse contexto.
O aviso de seleção inteligente sem áudio local fica preservado após reruns assíncronos.

## Resultado da implementação
97 testes Python aprovados. E2E Edge aprovado para limiar de escuta, pausas, seeks,
replay, limpeza, fila editável e reprodução MP3/WAV/FLAC. Regressão de biblioteca
mista, playlists inteligentes e isolamento de contas aprovada, sem erros JavaScript.
Áudio sintético, sem audição física e sem deploy público validado.

O player é renderizado antes dos painéis variáveis, com espaço fixo para feedback,
preservando a montagem do fragmento durante navegação. No Windows, gravações atômicas
repetem apenas PermissionError transitório até cinco vezes; falha persistente mantém
o arquivo anterior. Testes cobrem recuperação e preservação dos bytes originais.
