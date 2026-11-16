# Playlists inteligentes

Data: 2026-11-16
Pedido: implementar playlists inteligentes e registrar o pedido/resposta em prompts.md.

## Escopo
Evoluir o gerenciador existente em Python/Streamlit. Preservar playlists manuais,
reprodução, biblioteca e separação entre contas. Sem integrações externas ou reescrita.
Salvar definições declarativas no playlists.json já isolado por usuário, usando escrita
atômica e lock existentes. Não executar expressões Python nem código fornecido pelo usuário.

## Requisitos
1. Criar, pré-visualizar, editar nome/regras, excluir e reproduzir playlists inteligentes.
2. Usar de 1 a 20 regras, combinadas por todas (E) ou qualquer uma (OU).
3. Campos título, artista, álbum e gênero: contém, igual ou não contém; ignorar caixa/acentos.
4. Formato: igual ou diferente de MP3/WAV/FLAC; inferir extensão para registros antigos.
5. Duração: mínimo/máximo inclusivos, em segundos; rejeitar limites negativos ou não finitos.
6. Favorita e metadados incompletos: comparar Sim ou Não.
7. Ordenar por título, artista, álbum, duração ou formato; crescente ou decrescente.
8. Limitar a quantidade após seleção e ordenação; zero significa sem limite.
9. Recalcular contra a biblioteca atual ao consultar ou iniciar reprodução. Não salvar lista
   estática de resultados nem modificar a fila já iniciada a cada atualização de biblioteca.
10. Bloquear adição/remoção/reordenação manual de integrantes das inteligentes.
11. Preservar CRUD manual e não oferecer inteligentes no seletor de adição manual de faixas.
12. Garantir isolamento por conta para leitura, edição e exclusão.
13. Validar antes de gravar; uma alteração inválida não pode sobrescrever a definição salva.
14. Mostrar seleção vazia e erros de regras sem falha não tratada na interface.

## Modelo
Playlists manuais antigas continuam com id, name e track_ids.
Inteligentes acrescentam type=smart e definition, mantendo track_ids vazio para
compatibilidade. definition contém rules, match, sort, descending e limit.
Cada regra contém field, operator e value; valores são validados por campo.
Resultados não duplicam IDs. Desempate determinístico por título e ID.
Ausência de favorita equivale a falso. Duração inválida não corresponde a regra numérica.
Texto ausente equivale a vazio; não contém considera um texto ausente como não correspondente
à expressão buscada (logo satisfaz a negação). Nenhum metadado é inferido pela internet.

## Integração
core/smart_playlists.py: validação e avaliação pura de regras.
core/playlist.py: persistência de definição e resolução de playlists manuais/inteligentes.
ui/smart_playlists.py: editor, prévia, resultados, edição e reprodução no player existente.
app.py: seção inteligente e preservação dos controles manuais.

## Validação
Testes de regras: E/OU, acentos, operadores negativos, duração, favoritos, metadados,
ordenação, limites, duplicados, campos ausentes e definições inválidas.
Testes de persistência: CRUD, atualização dinâmica, compatibilidade manual e isolamento.
Testes de UI com Streamlit AppTest: prévia, criação, edição, exclusão e erro de nome vazio.
Comando: python -m unittest discover -s tests -v
A reprodução usa o mesmo player web já existente. Esta sessão não comprova deploy público.

## Limitações mantidas
Dados continuam temporários no Community Cloud por decisão anterior da dupla.
Inteligente significa seleção por regras, sem modelo de recomendação ou aprendizado.
Uma fila iniciada é uma seleção estável; para incorporar novas faixas, reproduzir novamente.
CLI OpenSpec indisponível conforme verificação anterior; SPEC registra esta especificação.

Resultado: 32 testes aprovados; integração da aba principal verificada com AppTest.
Contagem local dos quatro arquivos novos: 453 linhas com tokens Python, excluindo
comentários, docstrings e linhas vazias; 237 de implementação e 216 de testes.
Não equivale a relatório cloc. Sem commit, push ou deploy nesta sessão.
