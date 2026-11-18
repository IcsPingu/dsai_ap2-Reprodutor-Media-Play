# Design

## Context

Ver motivação em `proposal.md`. `core/library.py` armazena dicionários em JSON e as três rotas de importação usam `filepath` como chave. Links sem arquivo colidiriam nesse índice. A edição atual sempre tenta escrever ID3. `core/playlist.py` já guarda listas ordenadas de `track_ids`, suficientes para origens mistas.

`app.py` envia listas inteiras para o player na biblioteca, playlists e Play global. `AudioPlayer.play` também pode inserir diretamente uma faixa na fila; portanto filtrar somente a interface não protege todas as entradas. A playlist renderiza título/artista com HTML não escapado. Não há testes Python encontrados no repositório.

As especificações anteriores estão apenas na mudança concluída `wmp-audio-player`, não publicadas em `openspec/specs/`. Não arquivar nem reescrever esse trabalho nesta mudança.

## Goals / Non-Goals

**Goals:**
- Acrescentar campos ao modelo existente sem alterar IDs legados ou o formato das playlists.
- Concentrar validação e classificação de origens em lógica pura, testável sem rede.
- Separar a coleção organizada da fila efetivamente reproduzível.

**Non-Goals:**
- Não criar infraestrutura de provedores autenticados, banco de dados ou novo frontend.
- Preservar os dois mecanismos existentes: Pygame emite áudio no servidor e `st.audio` disponibiliza MP3s no navegador. Não redesenhar a sincronização entre esses controles nem adicionar streaming de serviços externos.
- Não prometer validar a existência da música no serviço nem equivalência de URLs diferentes da mesma música.

## Decisions

### 1. Evolução aditiva do registro de faixa

Usar `source_type` (`local` ou `external`), `platform` e `external_url`, mantendo título, artista, álbum, capa e demais campos existentes. Registros antigos sem `source_type` são locais; novos MP3s recebem a origem explicitamente. Links usam `filepath` vazio, duração desconhecida apresentada como indisponível e os mesmos valores padrão de metadados opcionais.

IDs externos usam prefixo `ext_` e hash SHA-256 da URL normalizada; não reutilizar o hash MD5 de caminhos locais. Duplicatas são detectadas pela URL normalizada, não por título. URL/origem são imutáveis na edição inicial; título vazio continua inválido.

Alternativa: criar armazenamento separado de links. Rejeitada porque duplicaria consultas e resolução de playlists.

### 2. URLs sem acesso remoto

Criar `core/sources.py` com `urllib.parse` e validação explícita. Aceitar apenas HTTPS, hostname DNS válido ou IP válido, porta válida e ausência de userinfo, controles, espaços internos ou barras invertidas. Normalizar whitespace externo, esquema/host em minúsculas, hostname internacional via IDNA, porta 443 omitida e fragmento removido. Preservar caminho e query, pois podem identificar a música.

Classificar por mapa explícito de hosts: `open.spotify.com`; `youtube.com`, `www.youtube.com`, `m.youtube.com`, `youtu.be`; `music.youtube.com`; `music.apple.com`; `deezer.com`, `www.deezer.com`; `soundcloud.com`, `www.soundcloud.com`; `tidal.com`, `www.tidal.com`, `listen.tidal.com`; `music.amazon.com`, `music.amazon.com.br`, `music.amazon.co.uk`. Demais hosts permanecem Link externo. Não usar comparação por substring nem seguir links curtos.

Revalidar URLs persistidas antes de criar ações clicáveis. Usar componentes nativos de link do Streamlit para abrir no navegador cliente, nunca `webbrowser.open` no servidor ou HTML interpolado.

Alternativa: buscar metadados/oEmbed ou resolver redirecionamentos. Adiada para evitar credenciais, SSRF e dependência de disponibilidade externa.

### 3. Preservação de dados durante importações

Substituir os índices globais por caminho nas importações por uma coleção que preserva todos os registros por ID e mantém um índice de caminhos apenas das faixas locais para deduplicação. Manter a ordem dos registros existentes e acrescentar novos itens.

Resolver caminhos locais somente para itens locais; capas continuam locais para ambas as origens. Na edição de links, salvar apenas JSON e eventual capa, sem tentar ID3. Não reescrever arquivos automaticamente durante simples carregamento.

Alternativa: atribuir um caminho artificial aos links. Rejeitada por confundir origem com localização de arquivo e deixar o player vulnerável a encaminhamento incorreto.

### 4. Coleção mista, fila local

Centralizar a identificação de faixas locais e a construção da fila filtrada. Aplicar em biblioteca, reprodução de playlists e fallback do Play global. Para seleção individual, localizar o MP3 escolhido por ID na fila filtrada, em vez de reutilizar o índice da lista mista.

No player, filtrar `set_queue` e guardar `original_queue` também somente com locais; rejeitar `play(external)` antes de qualquer mutação ou comando. Isso protege shuffle, avanço/retorno e repeat. Coleções sem locais geram aviso na UI e não chamam `set_queue`, preservando o áudio atual. Ao iniciar lote misto, informar a quantidade excluída; links só abrem por clique explícito.

Alternativa: fila híbrida que abre abas automaticamente. Rejeitada por pop-ups, falta de sincronização e falsa promessa de reprodução contínua entre serviços.

### 5. Interface e playlists

Acrescentar aba de cadastro por link na importação existente, com formulário em português. Biblioteca e playlists mostram origem e ação adequada; reusar adição/remoção por ID e manter ordenação. Não acrescentar sincronização, edição de URL ou uma interface nova de reordenação nesta etapa.

Usar texto nativo ou escaping para metadados em todos os componentes afetados, inclusive playlist e painel de faixa atual. Não inserir dados do usuário em HTML cru. Manter CSS e navegação existentes.

### 6. Verificação sem dispositivos ou dados reais

Criar testes com `unittest`, armazenamento temporário e mocks para ID3, uploads e comandos de áudio. Cobrir ambos os contratos das specs, incluindo todas as rotas de importação, IDs legados, round-trip de playlists, validação, deduplicação, edição externa e todas as entradas de reprodução. Usar Streamlit AppTest quando viável para formulários, fontes e avisos; completar ações de link com verificação manual no navegador.

## Risks / Trade-offs

- [Links genéricos podem não representar músicas ou estar indisponíveis] → Informar que são marcadores manuais, sem verificação de disponibilidade.
- [Queries distintas podem representar a mesma faixa] → Deduplicação conservadora; não remover parâmetros sem conhecimento do serviço.
- [Links HTTPS ainda podem levar a sites maliciosos] → Mostrar origem/hostname, abrir somente por ação explícita e não buscar conteúdo no servidor.
- [JSON compartilhado mantém limitações de concorrência e persistência do hosting] → Não anunciar isolamento por usuário ou sincronização; testes usam arquivos temporários.
- [Filtragem muda índices da fila] → Selecionar por ID e testar links antes/entre MP3s e shuffle.
- [Node local 20 está abaixo do requisito do CLI OpenSpec 2] → Os comandos de planejamento funcionaram via `npx`; recomendar Node compatível para uso contínuo sem alterar o runtime Python.

## Migration Plan

1. Na implementação, testar com cópias temporárias dos formatos legados; nunca modificar a biblioteca real durante testes.
2. Antes do primeiro uso da versão nova, orientar backup de `storage/library.json` e `storage/playlists.json`.
3. Carregar registros legados como locais, mantendo IDs; campos novos são gravados no próximo salvamento normal.
4. Validar importação após cadastro de múltiplos links e round-trip de playlist mista.
5. Para rollback, restaurar código e ambos os backups como conjunto: a versão antiga não entende links externos. Não executar downgrade automático que descarte registros.

## Integração autorizada em 2026-11-16

Os commits do colega até `77c4c96` introduzem contas, armazenamento isolado,
gravação atômica, MP3/WAV/FLAC, favoritos, filtros, player web sincronizado
por eventos e playlists inteligentes. Preservar esses mecanismos: o modelo
local agora inclui os três formatos, não somente MP3, e o player HTML5 próprio
substitui `st.audio` no modo web. As decisões históricas acima descrevem a
primeira implementação, não uma instrução para reverter o trabalho novo.

O cadastro externo usa `@serialized`, `scoped_path` e o salvamento atômico
existente. O mesmo link pode existir em contas diferentes sem compartilhar
metadados ou playlists. Capas externas também pertencem à conta.

Filtros e regras acrescentam origem local/externa e plataforma identificada
por URL validada. Links com duração desconhecida não satisfazem regras
numéricas de duração. Playlists inteligentes continuam dinâmicas e a fila
iniciada permanece um snapshot. A reprodução de seleções inteligentes usa
a mesma função de filtragem das playlists manuais; links são exibidos com
ações explícitas e nunca enviados ao componente de áudio.

Os testes existentes do colega são preservados. Os testes de links adotam
o login e armazenamento isolado; testes de navegador exercitam o componente
web real, usando contas temporárias e mídia sintética. Preservar o snapshot
Git de segurança até revisão; não criar commits ou push nesta integração.
