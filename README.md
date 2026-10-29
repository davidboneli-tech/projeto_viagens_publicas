# 🏛️ Análise de Viagens Públicas

Projeto avaliativo de Análise de Dados com Python — SCTEC, Turma T6.

**Autor:** David dos Santos Boneli

## 🎯 Objetivo

Construir um pipeline para baixar, armazenar, tratar e analisar dados de viagens a serviço do Governo Federal, utilizando a base de seis meses de 2025 disponibilizada pelo curso.

A solução permite analisar custos, pagamentos, duração das viagens e características dos deslocamentos.

## 🛠️ Tecnologias

- Python
- PostgreSQL
- SQL
- Pandas
- Matplotlib
- Jupyter Notebook no VS Code
- Git e GitHub

Bibliotecas adicionais: `gdown`, `psycopg2-binary` e `ipykernel`.

## 🗃️ Organização dos dados

| Camada | Finalidade | Tabelas |
|---|---|---|
| Raw | Preservar o conteúdo original dos CSVs como texto | raw_viagem, raw_pagamento, raw_passagem e raw_trecho |
| Silver | Converter tipos, remover duplicatas exatas e aplicar integridade relacional | silver_viagem, silver_pagamento, silver_passagem e silver_trecho |
| Gold | Consolidar indicadores para responder às perguntas de negócio | gold_indicadores e vw_gold_indicadores |

A tabela Gold armazena os indicadores no momento da atualização. A VIEW consulta a Silver atual.

## 📁 Arquivos

| Arquivo | Responsabilidade |
|---|---|
| config.py | Parâmetros e leitura das variáveis do .env |
| banco.py | Conexão e funções auxiliares do PostgreSQL |
| .env.example | Modelo de configuração sem credenciais reais |
| .gitignore | Exclusão de credenciais, dados e ambiente virtual do Git |
| requirements.txt | Dependências do projeto |
| 0_criar_banco.sql | Criação do banco e das oito tabelas Raw e Silver |
| 0_criar_banco.py | Executor auxiliar do script SQL pelo Python |
| 1_extrair.py | Download do ZIP e carga dos CSVs na Raw |
| 2_transformar.py | Tratamento e carga da Silver |
| 3_analise.ipynb | Consultas, gráficos, construção da Gold e conclusões |

O arquivo `.env` e a pasta `data/` são utilizados localmente e não são enviados ao GitHub.

## ⚙️ Como executar

### 1. Preparar o ambiente

Tenha o PostgreSQL instalado e em execução, além de Python, Git e VS Code com as extensões Python e Jupyter.

No terminal PowerShell:

```powershell
git clone https://github.com/davidboneli-tech/projeto_viagens_publicas.git
cd projeto_viagens_publicas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação, permita a execução somente na sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 2. Configurar a conexão

Copie o modelo:

```powershell
Copy-Item .env.example .env
```

Preencha o `.env` com host, porta, usuário, senha e nome do banco PostgreSQL.

O usuário informado deve possuir permissão para criar o banco e as tabelas.

Confira no `config.py` o `DRIVE_FILE_ID` do ZIP disponibilizado pelo curso.

### 3. Executar o pipeline

Na raiz do projeto, execute na ordem:

```powershell
python 0_criar_banco.py
python 1_extrair.py
python 2_transformar.py
```

A execução de `0_criar_banco.py` apaga e recria o banco `transparencia`,
incluindo todos os seus dados, tabelas e VIEWs. Feche as conexões abertas
com esse banco antes de executar. Após a recriação, execute novamente
a extração, a transformação e o notebook para reconstruir o pipeline.

### 4. Executar a análise

Abra `3_analise.ipynb` no VS Code, selecione o kernel da `.venv` e execute todas as células na ordem.

O notebook constrói a tabela e a VIEW Gold, valida os indicadores e apresenta as respostas com tabelas e gráficos.

Salve o notebook após a execução para manter os resultados disponíveis para leitura.

## 📐 Regras de tratamento

- Os CSVs são lidos diretamente do ZIP, em blocos, com separador `;` e codificação `latin-1`.
- A Raw mantém o conteúdo original, sem conversões de valores.
- Valores monetários são convertidos para Decimal; datas são convertidas para DATE.
- Valores ausentes permanecem NULL. Zero informado é preservado.
- Duplicatas são identificadas pela igualdade de todas as colunas da linha Raw antes da seleção dos campos da Silver.
- Chaves primárias, estrangeiras e constraints protegem a integridade da Silver.
- Custo líquido = diárias + passagens + outros gastos − devolução.
- Um componente monetário ausente resulta em custo líquido ausente.
- Duração = data final − data inicial. Viagens no mesmo dia possuem duração zero.
- Os destinos mantêm o texto completo da base, sem separação de roteiros nem rateio por cidade.
- Rankings de destinos e órgãos pagadores excluem ausências e descrições explícitas de sigilo.
- Pagamentos e trechos são agregados separadamente antes da consolidação, evitando multiplicação de valores.

## 📊 Perguntas de negócio

1. Quais são os cinco órgãos com maior custo total?
2. Quais são os três destinos com maior custo médio por viagem?
3. Qual é a viagem de maior duração e seu custo total?
4. Qual tipo de pagamento possui maior valor médio?
5. Qual meio de transporte é mais utilizado nos trechos?
6. Qual UF de destino aparece em mais trechos?
7. Qual órgão pagou mais no total?

As três primeiras perguntas são analisadas diretamente na Silver. As quatro restantes utilizam a Gold agregada.

O notebook apresenta seis gráficos e confere a equivalência entre os indicadores consolidados, a Silver e a VIEW.

## ✅ Resultados da carga

| Conjunto | Raw | Silver |
|---|---:|---:|
| Viagens | 341.860 | 341.860 |
| Pagamentos | 606.916 | 568.811 |
| Passagens | 167.260 | 167.210 |
| Trechos | 763.349 | 763.349 |

As diferenças em pagamentos e passagens decorrem da remoção de duplicatas exatas pelo critério adotado.

## 💡 Principais conclusões

- O Ministério da Justiça e Segurança Pública lidera o custo líquido por órgão superior, com R$ 486.933.121,65.
- O roteiro Abu Dabi, Riad e Rio de Janeiro apresenta o maior custo médio, de R$ 245.852,80, referente a uma viagem.
- A maior duração registrada é de 383 dias, com custo líquido de R$ 0,00. O registro merece conferência na fonte.
- PASSAGEM possui o maior valor médio por pagamento: R$ 1.856,78.
- Veículo Oficial é o meio mais frequente, com 386.424 trechos.
- São Paulo lidera os destinos por UF, com 82.722 trechos.
- Entre os órgãos identificados, o Fundo Nacional de Segurança Pública apresenta o maior total pago: R$ 141.911.719,64.

## ⚠️ Limitações

Os resultados representam o recorte disponibilizado pelo curso, sem extrapolação para o ano completo. Algumas viagens possuem datas que ultrapassam esse período.

Os três destinos com maior custo médio possuem uma viagem cada, limitando conclusões sobre padrões recorrentes.

Existem três custos líquidos negativos, preservados para investigação. Maior gasto ou valor atípico, isoladamente, não comprova irregularidade.

O ranking de órgãos identificados exclui 86.878 pagamentos sem identificação válida segundo os critérios adotados, somando R$ 170.659.883,35.

Os nomes dos órgãos pagadores são usados no agrupamento porque seu código não integra o modelo Silver definido. Eventos legítimos com conteúdo idêntico também não podem ser distinguidos pelo critério de deduplicação utilizado.

## 🔧 Possíveis melhorias

- Investigar registros atípicos junto à fonte dos dados.
- Registrar logs estruturados das cargas e transformações.
- Automatizar verificações de qualidade após cada carga.
- Comparar períodos adicionais quando houver dados disponíveis.
- Fixar versões das dependências após validar o ambiente completo.
