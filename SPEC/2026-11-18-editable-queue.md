# Fila de reprodução editável

Data: 2026-11-18
Pedido: Adicione ao prompts.md / faz uma fila de reprodução editável.

## Escopo
Evoluir AudioPlayer, app Streamlit e componente web existentes sem trocar stack.
Permitir tocar depois, adicionar ao final, mover próximas para cima/baixo, remover
ocorrência pendente e limpar próximas. Exibir duração estimada. Preservar áudio atual.

## Requisitos
1. Cada ocorrência tem _queue_id único, distinto do id da biblioteca; duplicatas são permitidas.
2. Tocar depois insere imediatamente após a atual; adicionar ao final preserva ordem anterior.
3. Adicionar na fila vazia seleciona a primeira faixa, sem iniciar automaticamente.
4. Apenas índices após a faixa atual podem ser movidos/removidos; proteger histórico e atual.
5. Limpar próximas preserva faixa atual, histórico e posição de reprodução.
6. Edições não enviam play/stop/seek nem incrementam a versão de comandos de transporte.
7. Separar queue_version de command_version; rejeitar feedback de versões antigas.
8. Navegador recebe atualizações da fila preservando HTMLAudioElement, src, posição,
   volume e pausa enquanto a ocorrência atual permanece na fila.
9. Feedback de navegação e aleatório deve devolver ordem de ocorrências e ocorrência atual.
10. Não permitir que feedback injete IDs desconhecidos; não remover arquivos da biblioteca.
11. Depois de uma edição explícita, a ordem resultante vira a base e desativa aleatório,
    evitando reaparecimento de faixas removidas ao alternar esse modo.
12. Calcular duração estimada das próximas a partir dos metadados; no navegador incluir
    restante da atual usando currentTime/duration reais. Valores inválidos equivalem a zero.
13. Tempo exibido desconsidera ciclos de repetição e é identificado como estimativa.
14. Fila continua por sessão, não compartilhada entre contas e não persistida em JSON.
15. Playlists manuais/inteligentes continuam iniciando filas pelo mesmo set_queue.

## Implementação
core/playback_queue.py contém operações de edição, validação de índices e feedback.
AudioPlayer herda essas operações e cria ocorrências em set_queue/play.
ui/queue_editor.py fornece controles na Biblioteca e na aba Tocando Agora.
O componente web diferencia atualização de fila de troca de transporte, com identidade
por ocorrência para tratar músicas repetidas sem selecionar a primeira cópia por engano.
Atualizações da fila não recarregam src da atual; relógio e pausa pertencem ao navegador.
A fila anterior é substituída quando uma playlist/biblioteca inteira é reproduzida de novo.

## Critérios de teste
- Inserção depois/final, duplicatas, mover, remover, limpar, proteção de índices.
- Preservar command_version, estado pausado e posição após edição.
- Sincronização de ordem do navegador e rejeição de feedback obsoleto/estranho.
- Duração ausente/inválida, isolamento entre instâncias e seleção da ocorrência correta.
- AppTest dos botões e duração da interface.
- E2E real: verificar src não recarregado e mesmo elemento de áudio após inserir,
  navegar entre abas, mover, remover e limpar; testar edição durante pausa.
- Reexecutar regressões de MP3/WAV/FLAC, repetição, seek e avanço de faixa.

## Limitações
Duração depende dos metadados e não inclui repetições futuras. Dados seguem temporários
no Streamlit Community Cloud por decisão anterior. Não houve pedido de commit/push nesta
etapa. Especificação em SPEC; CLI OpenSpec indisponível conforme diagnóstico anterior.


## Decisão de integração após teste real
O player foi colocado em um contêiner Streamlit estável, criado antes das seções
condicionais de navegação e preenchido ao final do script. Isso impede remontagem
do iframe ao alternar Biblioteca/Tocando Agora. Os testes verificam a identidade do
elemento de áudio e contam eventos loadstart, além de posição e estado pausado.
O E2E aguarda confirmação de queue_version após cada edição, evitando confundir
renderização assíncrona com resultado final da operação.


## Resultado final
50 testes Python aprovados. E2E Edge headless aprovado para edições durante reprodução
e pausa, navegação entre abas sem remontagem, três codecs e controles existentes.
420 linhas Python adicionadas, das quais 249 de testes, medidas com tokenize/AST e diff,
excluindo comentários, docstrings e vazias. HTML/JS e documentação fora dessa contagem.
Não equivale a relatório cloc. Sem commit, push ou comprovação do deploy nesta sessão.


## Compatibilidade com integração remota de plataformas
O merge preserva a biblioteca mista de links/arquivos. Apenas arquivos locais entram
na fila de áudio: set_queue filtra links e enqueue os rejeita. Links continuam com
abertura externa na biblioteca. Seleção da faixa local considera a posição original
na coleção mista; ocorrências repetidas continuam distintas por _queue_id.
