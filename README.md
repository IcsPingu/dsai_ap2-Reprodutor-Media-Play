# Reprodutor Media Play

Aplicação de reprodução e gerenciamento de músicas desenvolvida em Python com Streamlit.

O sistema permite importar músicas, organizar uma biblioteca, criar playlists, visualizar capas de álbuns e controlar a reprodução de áudio.

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
