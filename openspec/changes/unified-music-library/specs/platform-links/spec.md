# Spec Delta

## Purpose

Permitir registrar músicas de serviços externos na biblioteca e abrir seus links com segurança, sem apresentar esses registros como streaming integrado.

## ADDED Requirements

### Requirement: Cadastro manual de link musical
O sistema SHALL permitir cadastrar uma URL HTTPS com título obrigatório e artista/álbum opcionais, sem login, requisições remotas ou download de áudio.

#### Scenario: Cadastro e recarga
- **WHEN** o usuário cadastra um link válido com título e depois recarrega a biblioteca
- **THEN** o registro mantém seu ID, URL, título e origem, com valores padrão para metadados opcionais ausentes

#### Scenario: Título ausente
- **WHEN** o usuário envia um título vazio ou composto apenas por espaços
- **THEN** o cadastro é recusado com mensagem em português e sem alteração da biblioteca

### Requirement: Validação de URLs externas
O sistema SHALL aceitar somente URLs HTTPS absolutas com hostname válido, sem credenciais embutidas, espaços internos ou caracteres de controle; entradas inválidas SHALL ser recusadas sem alterar dados.

#### Scenario: URL insegura
- **WHEN** a entrada usa javascript, data, file, HTTP, caminho relativo, hostname ausente ou credenciais embutidas
- **THEN** o sistema informa erro de validação e não disponibiliza uma ação de abertura

### Requirement: Identificação da origem
O sistema SHALL identificar Spotify, YouTube, YouTube Music, Apple Music, Deezer, SoundCloud, Tidal e Amazon Music por hostnames explicitamente reconhecidos e classificar outros hosts válidos como Link externo.

#### Scenario: Serviços conhecidos e links genéricos
- **WHEN** o usuário registra URLs de open.spotify.com, music.youtube.com e um hostname não reconhecido
- **THEN** as origens são respectivamente Spotify, YouTube Music e Link externo

#### Scenario: Hostname enganoso
- **WHEN** uma URL contém um nome de serviço apenas no caminho ou em um hostname como open.spotify.com.example.org
- **THEN** o sistema não identifica essa URL como pertencente ao serviço

### Requirement: Identidade estável e prevenção de duplicatas
O sistema SHALL evitar duplicatas pela URL normalizada, ignorando espaços nas extremidades, caixa do hostname, porta HTTPS padrão e fragmento, preservando caminho e query.

#### Scenario: Reenvio equivalente
- **WHEN** o usuário envia novamente uma URL equivalente à já cadastrada
- **THEN** o sistema informa que ela já existe e preserva ID, metadados e referências em playlists

### Requirement: Abertura explícita no serviço
O sistema SHALL exibir origem e ação Abrir no serviço para links válidos na biblioteca e nas playlists; essa ação SHALL abrir a URL no navegador do usuário sem iniciar reprodução local.

#### Scenario: Abrir faixa externa
- **WHEN** o usuário aciona Abrir no serviço
- **THEN** o navegador abre a URL validada e a interface não informa que o áudio externo está sendo reproduzido pelo app

### Requirement: Edição de metadados externos
O sistema SHALL permitir editar os metadados e a capa local de um link sem acessar arquivos de áudio ou modificar seu ID, URL e origem.

#### Scenario: Alterar título de um link
- **WHEN** o usuário salva um novo título válido para um registro externo
- **THEN** a alteração persiste após recarga e não é realizada leitura ou escrita de tags ID3
