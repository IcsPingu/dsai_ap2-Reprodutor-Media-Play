# Proposal

## Why

A biblioteca atual organiza apenas MP3s locais, enquanto as músicas dos usuários estão distribuídas entre serviços. Registrar links junto aos arquivos locais e combiná-los nas mesmas playlists é um primeiro passo viável para um hub musical, sem prometer reprodução de serviços protegidos.

## What Changes

- Adicionar músicas por URL HTTPS, título obrigatório e artista/álbum opcionais, sem exigir contas ou APIs.
- Identificar serviços conhecidos pelo hostname e aceitar outros serviços como links externos genéricos.
- Exibir origem e ação adequada: reproduzir MP3 local ou abrir o serviço no navegador do usuário.
- Permitir playlists com arquivos locais e links, preservando ordem, IDs e persistência JSON.
- Proteger importações, edição de metadados e filas contra registros sem arquivo local.
- Manter a interface em português e o visual existente.
- Fora do escopo: streaming integrado, download de áudio, autenticação, busca remota, importação/sincronização de playlists dos serviços e metadados obtidos automaticamente.

## Capabilities

### New Capabilities

- `platform-links`: cadastro, validação, identificação de origem, persistência e abertura de links musicais.
- `unified-playlists`: organização de faixas locais e externas juntas, compatibilidade dos dados existentes e separação segura da reprodução local.

### Modified Capabilities

Nenhuma especificação principal publicada existe em `openspec/specs/`. As especificações do trabalho anterior permanecem em `openspec/changes/wmp-audio-player/`, ainda não arquivado; esta mudança acrescenta capacidades complementares sem alterar seus artefatos.

## Impact

- `core/library.py`: modelo de faixas, carregamento compatível, importações que preservam links e edição sem ID3 para links.
- Novo `core/sources.py`: validação/normalização de URLs e classificação de origem, sem requisições de rede.
- `core/playlist.py`: manter o formato existente de referências por `track_ids`.
- `core/player.py`, `app.py` e, se necessário, `ui/components.py`: impedir links no Pygame e apresentar ações por origem.
- `storage/library.json`: campos adicionais compatíveis, sem substituir IDs existentes; `storage/playlists.json` mantém seu formato.
- Testes automatizados novos, documentação de uso em `README.md` e registro da implementação em `prompts.md`.
- Sem novas dependências de produção previstas.
