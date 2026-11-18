# Reprodutor Media Play

Aplicação de reprodução e gerenciamento de músicas desenvolvida em Python com Streamlit.

O sistema permite importar músicas, organizar uma biblioteca, criar playlists, visualizar capas de álbuns e controlar a reprodução de áudio.

## Links de plataformas musicais

A biblioteca também pode guardar links HTTPS de músicas, com título informado
manualmente (artista e álbum são opcionais). O app reconhece Spotify, YouTube,
YouTube Music, Apple Music, Deezer, SoundCloud, Tidal e Amazon Music pelos hosts
listados em `core/sources.py`. Por exemplo, `https://open.spotify.com/track/123`
é Spotify e `https://music.youtube.com/watch?v=123` é YouTube Music.
Outros hosts HTTPS válidos aparecem como **Link externo**, por exemplo
`https://example.org/music/123`. Não há consulta de disponibilidade ou metadados,
login, download nem streaming integrado desses serviços.

São recusados links sem HTTPS, com credenciais, espaços internos, controles ou
hostname inválido. A validação não garante que um site seja seguro: confira o
hostname exibido antes de abrir. Hosts parecidos, como
`open.spotify.com.example.org`, não recebem a identificação Spotify.

URLs equivalentes não criam duplicatas: espaços externos, caixa do hostname,
porta 443 e fragmento são ignorados. Caminho e query são preservados; links
diferentes para a mesma música podem continuar sendo registros distintos.

### Compatibilidade e backup

Antes de usar esta versão, faça backup do diretório de dados das contas
(`storage/private` por padrão, ou `MEDIA_PLAY_DATA`). Preserve também os JSONs
legados `storage/library.json` e `storage/playlists.json`, se existirem.
Faixas antigas sem origem são tratadas como locais;
seus IDs e referências de playlists não mudam. O carregamento não reescreve
os arquivos: os campos adicionais são persistidos no próximo salvamento normal.
Importações locais preservam os links já cadastrados. Metadados de links são
editados apenas no JSON; nenhum arquivo de áudio é acessado para escrever tags.

Para voltar à versão anterior, restaure **o código e o backup de dados juntos**.
A versão antiga não entende registros externos. Não há migração destrutiva nem
remoção automática dos links para permitir downgrade. Contas autenticadas têm
biblioteca, links, capas e playlists separados. O mesmo link pode ter metadados
diferentes em contas diferentes. As escritas usam os locks e JSON atômico do
projeto; no hosting, a persistência ainda depende do disco disponível.

### Reprodução

Biblioteca e playlists podem misturar origens, mas **Reproduzir Áudios Locais**
monta uma fila apenas com MP3, WAV e FLAC locais e informa quantos links foram excluídos.
Os links são abertos manualmente no serviço, nunca automaticamente ao avançar
a fila. Uma coleção só de links não interrompe a reprodução local atual.

O modo web usa o componente de áudio do navegador implementado pelo colega:
play, pausa, seek e avanço usam eventos reais do elemento HTML5, sem tocar áudio
via Pygame no servidor. O modo local Pygame permanece disponível no código.
Links externos nunca são enviados ao componente de áudio. Isso não permite
streaming protegido nem garante persistência dos arquivos no Streamlit Cloud.

### Exemplo: uma playlist com três origens

1. Entre ou crie uma conta. Em **Importar Áudios → Link de Plataforma**, adicione
   `https://open.spotify.com/track/123` com um título.
2. Adicione `https://example.org/music/456` como link genérico.
3. Na aba de arquivos, importe um MP3, WAV ou FLAC seu.
4. Crie uma playlist em **Playlists** e use **+ Playlist** para os três itens
   na biblioteca. Eles permanecem juntos após recarregar.
5. Use **Abrir no serviço** para cada link ou **Reproduzir Áudios Locais da Playlist**
   para o arquivo local. Remover um item da playlist mantém a biblioteca.

Esses URLs ilustram o formato; não garantem músicas disponíveis nos destinos.
O fluxo foi verificado com MP3 silencioso e serviços interceptados, sem acesso
à biblioteca real. Comandos dos testes e limitações estão em `tests/README.md`.

### Origem e plataformas nas playlists inteligentes

Use os filtros **Origem** e **Plataforma** da biblioteca junto aos filtros de
favoritas, formato, artista e álbum. Nas playlists inteligentes, os novos campos
**Origem** e **Plataforma** aceitam comparações igual/diferente; por exemplo,
Origem = Link externo e Plataforma = Spotify.

Novos links compatíveis aparecem na próxima consulta, sem alterar a fila já
tocando. A seleção mostra ações para abrir os links. Reprodução inteligente
também exclui links com aviso; uma seleção só externa não interrompe o áudio.
Links não têm formato de áudio nem duração conhecida: não correspondem a
regras numéricas de duração. Plataforma é derivada da URL validada, não de um
rótulo salvo arbitrariamente. Integração documentada em
`SPEC/2026-11-16-platform-links-integration.md`.

## 🔗 URL

Site: https://media-play-desktop-fxudwyu8pcp2zsjafpha6n.streamlit.app/

## 👥 Dupla

- Adan Alexey
- Luiz Nicollas

## 🛠️ Stack

- **Python** — linguagem principal
- **Streamlit** — interface da aplicação
- **Pygame** — reprodução e controle de áudio
- **Mutagen** — leitura e edição de metadados ID3 dos arquivos MP3
- **Pillow** — processamento das capas dos álbuns
- **JSON** — armazenamento local da biblioteca e das playlists
- **Tkinter** — seleção de diretórios e arquivos

## ▶️ Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/lnicollas/dsai_ap1-Reprodutor-Media-Play.git
cd dsai_ap1-Reprodutor-Media-Play
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv .venv
```

Ative o ambiente:

```bash
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
streamlit run app.py
```

Após a execução, o Streamlit disponibilizará a aplicação no navegador.

## 🤖 Ferramentas

O desenvolvimento foi realizado com auxílio do **Google Antigravity**, utilizado como agente de IA durante a implementação, análise de problemas e evolução do projeto.

Para organizar o desenvolvimento assistido por IA, foi utilizado o **OpenSpec**, framework utilizado para especificação, planejamento e organização das alterações antes da implementação.

O projeto possui o registro dos prompts utilizados em `prompts.md` e as especificações do OpenSpec estão disponíveis na pasta `openspec/`.

## 🧠  IA

A IA utilizada durante o desenvolvimento foi através do agente Google Antigravity.

O modelo foi utilizado como apoio para:

- criação da estrutura inicial do projeto;
- implementação das funcionalidades;
- identificação e correção de erros;
- organização da arquitetura;
- desenvolvimento da interface;
- implementação do sistema de reprodução de áudio;
- gerenciamento da biblioteca e playlists;
- resolução de problemas durante o desenvolvimento.

## 📁 Estrutura principal

```text
├── app.py                  # Aplicação principal
├── core/
│   ├── library.py          # Biblioteca e metadados das músicas
│   ├── player.py           # Reprodução e controles de áudio
│   └── playlist.py         # Gerenciamento de playlists
├── ui/
│   └── components.py       # Componentes da interface
├── assets/
│   └── style.css           # Estilos da aplicação
├── storage/
│   ├── media/              # Arquivos de áudio
│   ├── covers/             # Capas dos álbuns
│   ├── library.json        # Dados da biblioteca
│   └── playlists.json      # Dados das playlists
├── openspec/               # Especificações do projeto
├── prompts.md              # Registro dos prompts utilizados
├── requirements.txt        # Dependências Python
└── packages.txt            # Dependências de sistema
```


## Formatos de áudio (AP2)

Importação por upload ou pasta: MP3, WAV e FLAC. Tags de MP3/WAV são ID3;
FLAC usa comentários Vorbis e suas imagens incorporadas. Sem tags, o nome do
arquivo é usado como título; não há identificação automática pela internet.
O navegador recebe o MIME de cada formato. A reprodução depende do suporte do
navegador ao codec do arquivo. A seleção de pasta nativa é destinada ao uso local.

Para executar os testes com áudio sintético (incluindo decodificação local):

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Especificação: [WAV e FLAC](SPEC/2026-11-13-wav-flac.md).


## AP2: contas e reprodução no navegador

O app continua em Python/Streamlit. Crie uma conta na tela inicial (usuário com
3 a 40 caracteres: letras sem acento, números, `_` ou `-`; senha de pelo menos
12 caracteres). Cada conta começa com biblioteca vazia e tem mídia, capas,
favoritos e playlists separados. Os arquivos originais de `storage/` são preservados.
Use upload na versão web; acesso a pastas do servidor fica desabilitado.

**Dados temporários no Streamlit Community Cloud:** por decisão da dupla, não há
armazenamento externo. Contas, uploads e playlists podem desaparecer em reinícios
ou redeploys. Mantenha os arquivos originais. O app exibe esse aviso no login e sidebar.
Localmente, `MEDIA_PLAY_DATA` permite escolher um diretório; o padrão é `storage/private`.
O SQLite contém somente contas; biblioteca e playlists continuam em JSON.

O áudio toca exclusivamente no navegador no modo web. Use os controles nativos
para play, pausa, posição e volume; os botões abaixo controlam anterior, próxima,
parada, aleatório e repetição. Se o navegador bloquear autoplay, clique em Play.
Filtros e favoritos estão na aba Biblioteca de Mídias.

### Testes e CI

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m pip install playwright
python -m playwright install chromium
python tests/browser_check.py
```

O teste de navegador cria dados e servidor temporários, encerrando-os ao terminar.
Opcionalmente, `BROWSER_EXECUTABLE` aponta para Chrome/Edge já instalado.
GitHub Actions roda testes Python em Windows/Ubuntu e navegador em Ubuntu a cada
push/PR. O workflow precisa ser enviado ao GitHub para aparecer em Actions.

### Publicação no Streamlit Community Cloud

1. Envie as alterações para o fork que pertence à dupla, preservando o histórico.
2. Configure o app do Community Cloud para esse fork, branch e `app.py`.
3. Aguarde instalar requirements e confirme o workflow verde no GitHub.
4. Abra a URL em duas sessões distintas; crie contas de teste e importe os três formatos.
5. Verifique play/pausa, seek, próxima, avanço automático, favoritos e isolamento.

Não reutilize a URL dos autores como evidência de deploy das alterações do fork.
A nova versão ainda precisa ser validada na URL pública. Não há dependência de Vercel.
Especificação: [Web, contas, biblioteca e CI](SPEC/2026-11-13-web-users-library.md).


## Playlists inteligentes

Na aba **Playlists**, abra **Criar playlist inteligente**, informe um nome e monte
as regras. Por exemplo: Favorita = Sim + Formato = FLAC, combinando **Todas (E)**.
Também é possível combinar artistas/gêneros por **Qualquer uma (OU)** e impor limites
de duração, ordenação e quantidade. Use **Pré-visualizar seleção** antes de salvar.

As regras ficam salvas na conta. Os resultados são recalculados a partir da biblioteca
atual; importar músicas ou mudar favoritas/metadados pode alterar a seleção seguinte.
Use **Reproduzir seleção inteligente** para iniciar a fila. A fila em execução não é
alterada automaticamente. Para modificar integrantes, edite as regras; playlists manuais
continuam com adição/remoção individual na seção separada da mesma aba.

Especificação: [Playlists inteligentes](SPEC/2026-11-16-smart-playlists.md).


## Fila editável

Na Biblioteca, abra **Adicionar à fila** e escolha **Tocar depois** ou **Adicionar ao
final**. É possível enfileirar a mesma música mais de uma vez. Na aba **Tocando Agora**,
use **Subir**, **Descer** e **Remover da fila** nas próximas faixas. **Limpar próximas**
mantém a atual e o histórico. Essas ações não excluem músicas nem alteram playlists.

A atual e as anteriores ficam protegidas. Uma edição mantém posição, pausa e volume;
se a fila estiver vazia, adicionar seleciona a primeira faixa sem autoplay. Uma edição
explícita desativa aleatório e preserva a ordem visível como nova base. O tempo restante
é estimado, não inclui ciclos de repetição e usa zero para durações inválidas.
A fila fica somente na sessão. Reproduzir uma playlist inteira substitui a fila.

Especificação: [Fila editável](SPEC/2026-11-18-editable-queue.md).
