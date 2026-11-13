# Evolução incremental: web, contas, organização e CI

Data: 2026-11-13
Responsáveis: David Tavares e João Gonçalves

## Pedido e decisões confirmadas
Concluir WAV/FLAC e CI; corrigir reprodução web; separar biblioteca por usuário;
adicionar favoritos, filtros e ordenação. Preservar Python, Streamlit, módulos e dados originais.
O cliente confirmou nesta sessão: continuar com Streamlit Community Cloud e aceitar
contas e arquivos temporários. Não contratar nem integrar armazenamento externo.
A exigência inicial de persistência durável foi substituída por essa decisão explícita.
Sem reescrita de framework, novo repositório ou alteração de histórico.

## Evidências anteriores à mudança
O motor estimava progresso pelo relógio do servidor e chamava pygame em servidor.
O st.audio tinha controles próprios independentes. library.json e playlists.json eram globais.
Havia sete testes de formatos, sem workflow do GitHub Actions.

## Requisitos e critérios de aceitação
### Áudio web
- O navegador deve ser a autoridade de posição, pausa e fim de faixa.
- Play, pausa, seek e volume devem usar controles do elemento HTML audio.
- Anterior, próxima e parar devem agir sobre esse mesmo elemento.
- Fim da faixa deve avançar pela fila, respeitando repetição desligada, todas ou uma.
- Aleatório deve embaralhar a fila sem reiniciar a faixa atual.
- Interações não relacionadas no Streamlit não devem reiniciar o áudio.
- Bloqueio de autoplay e falha de codec devem ter mensagens visíveis.
- MP3, WAV e FLAC devem ser validados com arquivos sintéticos reais no navegador.

### Contas e dados
- Cadastro e login devem preceder toda leitura de biblioteca na aplicação web.
- Senhas devem usar PBKDF2-HMAC-SHA256, sal aleatório e comparação em tempo constante.
- Contas ficam em SQLite separado; biblioteca e playlists permanecem em JSON.
- Cada identidade autenticada deve ter diretório próprio, incluindo mídia e capas.
- Contexto do usuário deve ser local à execução, sem trocar constantes globais entre sessões.
- Caminhos de outra conta devem ser recusados; varredura de pastas do servidor fica desativada.
- Logout deve limpar estado da sessão e desmontar o componente de áudio.
- Escrita de JSON deve ser atômica; operações concorrentes no mesmo processo são serializadas.
- Dados originais de storage permanecem preservados, sem serem copiados a contas novas.
- No Community Cloud os dados são temporários; avisar no login e barra lateral.
- MEDIA_PLAY_DATA permite escolher diretório local. Isso não transforma disco efêmero em durável.

### Organização
- Favoritos devem ser salvos no JSON da conta e sobreviver a reruns e novo login enquanto o disco existir.
- Busca deve ignorar caixa e acentos.
- Filtros combináveis: formato, artista, álbum, favoritas e metadados incompletos.
- Ordenação por título, artista, álbum, duração numérica e formato, crescente ou decrescente.
- Itens antigos sem campo format devem inferir formato pela extensão.
- Artista ou álbum vazio/desconhecido deve marcar metadados incompletos.

### CI
- GitHub Actions em push, pull_request e execução manual.
- Testes Python em Ubuntu e Windows, Python 3.13.
- Job de navegador Chromium com instalação de dependências Playwright.
- O resultado remoto só será declarado verde depois de execução no GitHub.

## Implementação
core/user_storage.py: contas, contexto, caminhos e gravação atômica.
core/library.py e core/playlist.py: caminhos calculados por conta, mantendo API legada.
core/player.py: modo browser sem pygame e sem estimativa temporal do progresso.
ui/browser_player.py e ui/browser_player/index.html: componente bidirecional persistente
com áudio nativo, fila no navegador e eventos para sincronizar a seleção no Python.
core/library_filters.py: consultas puras; app.py: autenticação, filtros e favoritos.
Componentes existentes e motor local pygame continuam presentes, sem substituir o projeto.

## Validação e limites
11 testes de unidade/integração cobrem áudio real, tags, capas, autenticação,
isolamento entre contas e threads e filtros combinados. Teste E2E usa servidor
Streamlit temporário e navegador real, sem substituir o áudio por mocks.
Áudio de teste é sintético; não há comprovação de audição humana.
O componente envia a fila em base64: adequado à demonstração, com consumo de memória
proporcional ao tamanho total. Otimização por streaming está fora desta entrega.
Esta implementação é de um processo Streamlit. Os locks não coordenam múltiplas réplicas.
Sem recuperação de senha ou identidade externa. Sessões recarregadas exigem novo login.
Sem armazenamento durável por escolha explícita do cliente.
Deploy público e resultado remoto de CI dependem de envio ao GitHub e acesso ao deploy.

## Checklist
- [x] Manter MP3/WAV/FLAC e testes existentes.
- [x] Criar controles web baseados em eventos do áudio.
- [x] Implementar contas e isolamento de mídia/playlists/capas.
- [x] Implementar favoritos e filtros combinados.
- [x] Criar workflow de CI para testes Python e navegador.
- [x] Informar dados temporários por decisão do cliente.
- [x] Confirmar CI verde no GitHub após envio (commit afe45c5, execução 43498971813).
- [ ] Validar a nova versão na URL pública após deploy.


## Evidência local final
11 testes Python aprovados. E2E aprovado em Edge headless com os três codecs,
transporte, ended, repetição uma/todas, aleatório e rerun durante filtros.
Captura local: artifacts/browser-library.png (artefato de teste, fora do versionamento).
Tema escuro nativo configurado em .streamlit/config.toml após revisão visual.
Essa evidência não substitui execução do CI remoto ou validação do deploy público.

CI remoto aprovado: https://github.com/IcsPingu/dsai_ap2-Reprodutor-Media-Play/actions/runs/43498971813 (Windows, Ubuntu e Chromium). Deploy público pendente de URL do fork.
