# Integração de links com contas e playlists inteligentes

## Pedido e base

Integrar o trabalho local ainda não commitado de links musicais com os commits
do colega até `77c4c96`, sem criar commit ou push. Preservar WAV/FLAC/MP3, contas,
favoritos, filtros, isolamento, player web, playlists inteligentes e CI.
Planejamento e requisitos complementares ficam em
`openspec/changes/unified-music-library/`, seção de integração.

## Contrato

1. Links são marcadores HTTPS manuais, não downloads ou streaming integrado.
2. Cadastro, edição, capas e playlists usam o namespace da conta, escrita
   atômica e lock por conta. Deduplicação é por URL normalizada dentro da conta.
3. Importações de MP3/WAV/FLAC mantêm todos os registros externos e referências.
   O parser valida uploads sem nome, inclusive MP3 MPEG-2.5, e rejeita corrupção
   ou conteúdo incompatível com a extensão.
4. Metadados externos não acessam tags de áudio. Usuários diferentes podem usar
   o mesmo ID derivado da URL sem compartilhar dados; suas coleções são isoladas.
5. Biblioteca e regras inteligentes acrescentam Origem e Plataforma. Plataforma
   é calculada pela URL validada; hosts desconhecidos continuam Link externo.
6. Comparações de Origem/Plataforma aceitam igual/diferente. Regras existentes
   e combinações E/OU, ordenação, limites e avaliação dinâmica são preservadas.
7. Links não têm formato de áudio nem duração conhecida. Regras de duração não
   os selecionam; uma regra negativa de formato ainda pode incluí-los por não
   serem daquele formato. Use Origem = Local para restringir a arquivos.
8. Biblioteca e playlists manuais/inteligentes exibem ações explícitas de abrir
   serviço, sem HTML executável em metadados e sem abertura automática.
9. Todas as filas de áudio contêm apenas arquivos locais. Seleção inteligente
   mista avisa quantos links foram excluídos; seleção somente externa não altera
   a fila, versão de comando ou faixa em execução.
10. O componente web do colega é preservado e rejeita registros externos mesmo
    se fornecidos diretamente à sua fila. Filtros da biblioteca não reiniciam
    a reprodução. Dados permanecem temporários no Community Cloud.

## Validação

- Suíte combinada `python -m unittest discover -s tests`: testes do colega e
  regressões de links, incluindo contas, concorrência, formatos reais e AppTest.
- `python tests/browser_check.py`: transporte web e codecs MP3/WAV/FLAC.
- `python tests/browser_flow.py`: conta temporária, links + uploads, playlist
  manual/inteligente, edição, abertura interceptada e isolamento de outra conta.
- Compilação, diff sem conflitos e validação OpenSpec.
- Evidências finais e limitações registradas em `tests/README.md` e `prompts.md`.

Não comprova streaming externo, disponibilidade de serviços, persistência
durável, CI remoto ou deploy público.
