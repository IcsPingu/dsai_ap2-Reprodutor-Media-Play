# Tasks

## 1. Origens e URLs

- [x] 1.1 Criar `core/sources.py` com validação HTTPS, normalização, classificação por hosts explícitos e identificação de origem local/externa; verificar com testes `unittest` para cada serviço, host genérico, host enganoso, credenciais, esquemas inseguros, controles, portas e equivalência de URLs.
- [x] 1.2 Documentar no `README.md` os serviços reconhecidos, fallback genérico e limites de validação/deduplicação; conferir exemplos contra os testes de URLs.

## 2. Biblioteca compatível

- [x] 2.1 Acrescentar campos de origem e cadastro externo com ID estável, título obrigatório e deduplicação; verificar round-trip JSON, rejeições sem escrita e preservação de IDs/metadados legados em armazenamento temporário.
- [x] 2.2 Refatorar importação física, uploads e varredura para indexar caminhos somente de faixas locais preservando links; testar cada rota com dois links pré-existentes e referências de playlist.
- [x] 2.3 Separar edição externa de escrita ID3 e manter capas locais; testar alteração de metadados/capa sem acesso ID3 e sem mudança de ID, URL ou origem.
- [x] 2.4 Documentar no `README.md` compatibilidade, backup dos dois JSONs e rollback conjunto; verificar que os procedimentos não exigem migração destrutiva.

## 3. Proteção da reprodução local

- [x] 3.1 Filtrar filas e `original_queue` no player, rejeitar reprodução direta de links antes de mutações e selecionar locais por ID após filtragem; testar com motor mockado seleção após links, shuffle, repeat, avanço, retorno e preservação da faixa atual ao rejeitar link.
- [x] 3.2 Preparar lógica compartilhada para iniciar coleções locais e calcular links excluídos; testar biblioteca/playlist mista, coleção somente externa e fallback do Play global sem modificar a fila quando não houver locais.
- [x] 3.3 Documentar no `README.md` que reprodução em lote exclui links e que Pygame emite áudio no servidor; conferir que o texto distingue o `st.audio` existente de streaming integrado de serviços.

## 4. Interface e playlists mistas

- [x] 4.1 Adicionar formulário de link na área de importação com mensagens em português e atualização de sessão; verificar via AppTest ou teste manual documentado cadastro válido, título vazio, URL inválida e duplicata.
- [x] 4.2 Exibir origem/hostname e links nativos revalidados na biblioteca e playlists; usar ações de Play somente para locais e texto seguro para metadados nos componentes afetados; verificar links conhecidos/genéricos, URL persistida inválida e título com HTML sem execução.
- [x] 4.3 Integrar reprodução filtrada e avisos em todos os pontos de entrada de `app.py`; verificar seleção individual correta, contagem de links excluídos e ausência de alterações de reprodução em coleção somente externa.
- [x] 4.4 Reusar `track_ids` para playlists mistas e testar criação, renomeação, ordem, remoção, duplicata e recarga; verificar que remover um link da playlist mantém sua entrada na biblioteca.
- [x] 4.5 Acrescentar ao `README.md` um exemplo de MP3 + link conhecido + link genérico na mesma playlist e registrar o pedido/resultado real em `prompts.md`; executar o exemplo e não registrar como concluído algo não verificado.

## 5. Verificação integrada

- [x] 5.1 Executar `python -m unittest discover -s tests` e `python -m compileall app.py core ui tests`; confirmar sucesso sem usar armazenamento real, rede ou dispositivo de áudio nos testes automatizados.
- [x] 5.2 Executar fluxo completo no navegador: cadastrar dois links, importar MP3, criar playlist mista, recarregar, editar metadados, abrir serviço, reproduzir locais e remover item; registrar resultados e limitações, incluindo regressão de importação após cadastro dos links.
- [x] 5.3 Validar os artefatos com `npx --yes @fission-ai/openspec validate unified-music-library --strict` e revisar `git diff` para confirmar que nenhum JSON real ou artefato do colega foi alterado pelos testes.

## 6. Integração com os commits do colega (2026-11-16)

- [x] 6.1 Integrar os commits até `77c4c96` preservando links, contas, gravação atômica e MP3/WAV/FLAC; verificar importações mistas, edição externa sem tags e isolamento entre duas contas com os testes combinados.
- [x] 6.2 Integrar origens na busca e regras de playlists inteligentes e proteger filas no player web; verificar filtros por origem/plataforma, prévia dinâmica, links sem duração, avisos e coleção sem áudio sem interromper reprodução.
- [x] 6.3 Adaptar os testes AppTest e de navegador ao login e player web do colega; verificar cadastro/login, biblioteca mista, formatos, playlist inteligente, abertura externa, transporte de áudio e isolamento sem usar dados reais.
- [x] 6.4 Atualizar README, SPEC e prompts com compatibilidade e evidências; executar suíte combinada, compilação, navegador e validação OpenSpec, conferir ausência de conflitos e manter tudo sem commit/push.

## Workflow follow-up

- Revisar a implementação e os resultados de verificação antes de solicitar arquivamento desta mudança.
- Tratar a publicação/arquivamento da mudança anterior `wmp-audio-player` separadamente, sem alterar seu histórico nesta implementação.
