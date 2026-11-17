# Verificação da biblioteca unificada

## Testes automatizados

Na raiz, usando o ambiente virtual:

```powershell
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m unittest discover -s tests
.venv\Scripts\python -m compileall app.py core ui tests
```

Os testes usam diretórios temporários e mocks de áudio/ID3. Incluem validação de
URLs, hosts enganosos, deduplicação, formatos legados, todas as rotas de importação,
edição/capas, playlists e navegação/repeat/shuffle. AppTest exercita os formulários,
as ações por origem e os pontos de entrada da reprodução sem abrir dispositivo
de áudio ou consultar serviços.

## Navegador (opcional)

Requer as dependências de desenvolvimento e Playwright:

```powershell
.venv\Scripts\python -m pip install playwright
.venv\Scripts\python -m playwright install chromium
.venv\Scripts\python tests/browser_check.py
.venv\Scripts\python tests/browser_flow.py
```

Os scripts iniciam servidores temporários de `app.py` com `MEDIA_PLAY_DATA`
isolado. `browser_check.py` verifica os codecs e controles do player do colega.
`browser_flow.py` cria conta pela UI, cadastra links Spotify/genérico, importa
MP3/WAV/FLAC silenciosos e cria/recarrega uma playlist mista. Verifica edição,
abertura em nova aba, regras inteligentes por origem, reprodução no componente
web, remoção sem excluir a biblioteca e isolamento de uma segunda conta.
Os servidores são encerrados ao terminar. Não há bypass de login.

Resultados, log e screenshot são salvos em
`%LOCALAPPDATA%\Temp\opencode\unified-music-verification` no Windows ou
`<temp>/opencode/unified-music-verification` em outros sistemas.
O teste do colega também grava screenshot em `artifacts/`.
Os JSONs reais e as especificações do trabalho anterior não são usados.

## Evidência e limites

- A suíte integrada passou 61 testes Python/AppTest, preservando os testes do
  colega e acrescentando regressões de contas, formatos, regras e player web.
  A primeira implementação havia passado 18 testes.
- A navegação para Spotify foi interceptada: comprova destino e abertura no
  cliente, não disponibilidade do serviço, login ou streaming externo.
- Saída física não foi ouvida. O modo web não inicia Pygame no servidor;
  o teste de decoder usa o driver dummy, e o teste integrado usa áudio silencioso.
- AppTest pode registrar `missing ScriptRunContext` em modo de teste e o
  Streamlit atual avisa sobre `use_container_width` nos componentes existentes.
- A primeira versão de navegador precisava esperar o salvamento real de cada
  adição à playlist, em vez de reutilizar um toast antigo como confirmação.
- Os dois testes Chromium passaram na versão integrada. `browser_flow.py`
  confirmou cadastro/login, links + três formatos, recarga, edição, abertura
  interceptada, playlist inteligente sem interromper áudio e segunda conta
  isolada, com `page_errors: []`.
- Seletores React Aria do Streamlit atual exigem abrir explicitamente o menu
  após pesquisar: texto digitado no combobox sozinho não confirma a regra.
- CSS/tema do colega foram preservados; não é uma revisão de acessibilidade.
