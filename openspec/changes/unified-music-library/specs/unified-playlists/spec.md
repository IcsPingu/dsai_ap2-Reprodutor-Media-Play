# Spec Delta

## Purpose

Organizar músicas locais e links externos nas mesmas playlists, preservando os dados existentes e distinguindo organização musical de reprodução local.

## ADDED Requirements

### Requirement: Playlists com origens mistas
O sistema SHALL permitir adicionar e remover faixas locais e externas na mesma playlist, preservando a ordem de inserção e impedindo repetição do mesmo ID.

#### Scenario: Persistir playlist mista
- **WHEN** o usuário adiciona um MP3, um link Spotify e um link genérico e recarrega a playlist
- **THEN** os três itens reaparecem na mesma ordem com suas origens e ações apropriadas

#### Scenario: Adicionar novamente ou remover um link
- **WHEN** o usuário tenta adicionar novamente o mesmo ID e depois remove esse item
- **THEN** nenhuma duplicata é criada e a remoção da playlist não exclui o registro da biblioteca

### Requirement: Compatibilidade com dados locais existentes
O sistema SHALL tratar faixas legadas sem indicação de origem como locais e preservar seus IDs, metadados e referências de playlist ao carregar e salvar dados mistos.

#### Scenario: Abrir biblioteca anterior à mudança
- **WHEN** uma biblioteca e playlists locais existentes são carregadas e um link é adicionado
- **THEN** os MP3s continuam identificados pelos mesmos IDs e suas playlists continuam válidas

### Requirement: Importações locais preservam registros externos
O sistema SHALL preservar todos os links e referências de playlists durante importação de arquivos, upload e varredura de diretórios locais.

#### Scenario: Importar depois de salvar vários links
- **WHEN** a biblioteca contém dois links distintos e o usuário importa ou escaneia MP3s
- **THEN** ambos os links e as referências aos seus IDs permanecem intactos junto aos arquivos importados

### Requirement: Reprodução em lote restrita a faixas locais
O sistema SHALL montar filas somente com faixas locais, preservando sua ordem relativa antes de aplicar shuffle e informando a quantidade de links excluídos. Essa regra SHALL valer para biblioteca, playlists e Play global.

#### Scenario: Reproduzir playlist mista
- **WHEN** o usuário solicita reprodução local de uma playlist com dois MP3s e três links
- **THEN** a fila contém apenas os dois MP3s e a interface informa que três links devem ser abertos nos serviços

#### Scenario: Coleção sem MP3s
- **WHEN** o usuário tenta reproduzir uma coleção contendo somente links
- **THEN** o sistema informa que não há faixas locais, não altera a reprodução atual e não abre links automaticamente

### Requirement: Seleção e controles locais seguros
O sistema SHALL reproduzir o MP3 selecionado mesmo quando links o antecedem na lista, e SHALL impedir que links entrem na fila por seleção direta, avanço, retorno, repetição ou shuffle.

#### Scenario: Seleção após item externo
- **WHEN** o usuário seleciona um MP3 precedido por links na biblioteca
- **THEN** o MP3 escolhido inicia e os índices da fila local permanecem corretos

#### Scenario: Tentativa direta de reproduzir link
- **WHEN** um registro externo é enviado à reprodução local
- **THEN** a solicitação é recusada sem comandos ao motor de áudio nem alteração da faixa local em execução

### Requirement: Exibição segura dos metadados
O sistema SHALL exibir títulos, artistas e demais metadados fornecidos pelo usuário como texto, sem interpretá-los como HTML executável.

#### Scenario: Metadado contendo marcação
- **WHEN** um título ou artista contém marcação HTML
- **THEN** biblioteca e playlist exibem esse valor como texto sem executar a marcação

### Requirement: Isolamento de links por conta
O sistema SHALL manter links, metadados, capas e playlists no armazenamento da conta autenticada, preservando o isolamento já existente para MP3, WAV e FLAC.

#### Scenario: Mesmo link em duas contas
- **WHEN** duas contas cadastram a mesma URL com títulos diferentes
- **THEN** cada conta visualiza e edita somente seus próprios dados, sem alterar a outra

### Requirement: Filtros e regras por origem
O sistema SHALL permitir filtrar a biblioteca e definir regras inteligentes por origem local/externa e plataforma, mantendo os filtros e regras já existentes.

#### Scenario: Seleção dinâmica de plataforma
- **WHEN** uma playlist inteligente seleciona Spotify e uma nova faixa Spotify é cadastrada
- **THEN** a consulta seguinte inclui o novo registro sem modificar uma fila em execução

#### Scenario: Duração externa desconhecida
- **WHEN** uma regra exige duração máxima ou mínima para um registro externo sem duração
- **THEN** esse registro não satisfaz a regra numérica

### Requirement: Reprodução inteligente e múltiplos formatos
O sistema SHALL aplicar a política de fila local também às playlists inteligentes e ao player web, aceitando MP3, WAV e FLAC locais e informando os links excluídos.

#### Scenario: Playlist inteligente sem arquivos de áudio
- **WHEN** o usuário solicita reprodução de uma seleção inteligente somente com links
- **THEN** o app mostra um aviso e preserva a faixa e fila atuais sem abrir serviços automaticamente
