-- Apaga o banco existente e recria sua estrutura do zero.
DROP DATABASE IF EXISTS transparencia;
CREATE DATABASE transparencia;

-- CAMADA RAW: preserva os valores originais dos CSVs.
-- VARCHAR sem tamanho máximo evita cortar textos na importação.

CREATE TABLE raw_viagem (
    id_viagem VARCHAR,                 -- Identificador do processo de viagem
    num_proposta VARCHAR,              -- Número da proposta PCDP
    situacao VARCHAR,                  -- Situação da viagem
    viagem_urgente VARCHAR,            -- Indicação de urgência
    justificativa_urgencia VARCHAR,     -- Justificativa da urgência
    cod_orgao_superior VARCHAR,         -- Código do órgão superior
    nome_orgao_superior VARCHAR,        -- Nome do órgão superior
    cod_orgao_solicitante VARCHAR,      -- Código do órgão solicitante
    nome_orgao_solicitante VARCHAR,     -- Nome do órgão solicitante
    cpf_viajante VARCHAR,              -- CPF no formato original
    nome_viajante VARCHAR,             -- Nome do viajante
    cargo VARCHAR,                     -- Cargo do viajante
    funcao VARCHAR,                    -- Função do viajante
    descricao_funcao VARCHAR,          -- Descrição da função
    data_inicio VARCHAR,              -- Data inicial como texto
    data_fim VARCHAR,                 -- Data final como texto
    destinos VARCHAR,                 -- Destinos informados
    motivo VARCHAR,                   -- Motivo da viagem
    valor_diarias VARCHAR,            -- Valor original das diárias
    valor_passagens VARCHAR,          -- Valor original das passagens
    valor_devolucao VARCHAR,          -- Valor original da devolução
    valor_outros_gastos VARCHAR       -- Valor original dos demais gastos
);

CREATE TABLE raw_pagamento (
    id_viagem VARCHAR,                 -- Identificador do processo de viagem
    num_proposta VARCHAR,              -- Número da proposta PCDP
    cod_orgao_superior VARCHAR,         -- Código do órgão superior
    nome_orgao_superior VARCHAR,        -- Nome do órgão superior
    cod_orgao_pagador VARCHAR,          -- Código do órgão pagador
    nome_orgao_pagador VARCHAR,         -- Nome do órgão pagador
    cod_ug_pagadora VARCHAR,            -- Código da unidade gestora pagadora
    nome_ug_pagadora VARCHAR,           -- Nome da unidade gestora pagadora
    tipo_pagamento VARCHAR,            -- Tipo de pagamento
    valor VARCHAR                      -- Valor original do pagamento
);

CREATE TABLE raw_passagem (
    id_viagem VARCHAR,                 -- Identificador do processo de viagem
    num_proposta VARCHAR,              -- Número da proposta PCDP
    meio_transporte VARCHAR,           -- Meio de transporte
    pais_origem_ida VARCHAR,           -- País de origem da ida
    uf_origem_ida VARCHAR,             -- UF de origem da ida
    cidade_origem_ida VARCHAR,         -- Cidade de origem da ida
    pais_destino_ida VARCHAR,          -- País de destino da ida
    uf_destino_ida VARCHAR,            -- UF de destino da ida
    cidade_destino_ida VARCHAR,        -- Cidade de destino da ida
    pais_origem_volta VARCHAR,         -- País de origem da volta
    uf_origem_volta VARCHAR,           -- UF de origem da volta
    cidade_origem_volta VARCHAR,       -- Cidade de origem da volta
    pais_destino_volta VARCHAR,        -- País de destino da volta
    uf_destino_volta VARCHAR,          -- UF de destino da volta
    cidade_destino_volta VARCHAR,      -- Cidade de destino da volta
    valor_passagem VARCHAR,           -- Valor original da passagem
    taxa_servico VARCHAR,             -- Taxa original de serviço
    data_emissao VARCHAR,             -- Data da emissão ou compra
    hora_emissao VARCHAR              -- Hora da emissão ou compra
);

CREATE TABLE raw_trecho (
    id_viagem VARCHAR,                 -- Identificador do processo de viagem
    num_proposta VARCHAR,              -- Número da proposta PCDP
    sequencia_trecho VARCHAR,          -- Sequência do trecho
    origem_data VARCHAR,              -- Data de origem
    origem_pais VARCHAR,              -- País de origem
    origem_uf VARCHAR,                -- UF de origem
    origem_cidade VARCHAR,            -- Cidade de origem
    destino_data VARCHAR,             -- Data de destino
    destino_pais VARCHAR,             -- País de destino
    destino_uf VARCHAR,               -- UF de destino
    destino_cidade VARCHAR,           -- Cidade de destino
    meio_transporte VARCHAR,          -- Meio de transporte
    numero_diarias VARCHAR,           -- Número original de diárias
    missao VARCHAR                    -- Indicação de missão
);

-- CAMADA SILVER: dados tratados e com tipos definidos.
-- SERIAL é o incremento automático de identificadores no PostgreSQL.

CREATE TABLE silver_viagem (
    id_viagem VARCHAR(20) PRIMARY KEY NOT NULL, -- Identificador único da viagem
    num_proposta VARCHAR(20),                  -- Número da proposta PCDP
    situacao VARCHAR(50),                      -- Situação da viagem
    viagem_urgente VARCHAR(5),                 -- Indicação de urgência
    cod_orgao_superior VARCHAR(20),            -- Código do órgão superior
    nome_orgao_superior VARCHAR(255) NOT NULL, -- Nome obrigatório
    nome_viajante VARCHAR(255),                -- Nome do viajante
    cargo VARCHAR(255),                        -- Cargo do viajante
    data_inicio DATE,                         -- Data inicial convertida
    data_fim DATE,                            -- Data final convertida
    destinos VARCHAR(4000),                    -- Destinos informados
    motivo VARCHAR(4000),                      -- Motivo da viagem
    valor_diarias DECIMAL(10, 2) CHECK (valor_diarias >= 0), -- Diárias não negativas
    valor_passagens DECIMAL(10, 2),            -- Valor das passagens
    valor_devolucao DECIMAL(10, 2),             -- Valor devolvido
    valor_outros_gastos DECIMAL(10, 2),         -- Demais gastos
    valor_total DECIMAL(12, 2),                -- Calculado na transformação
    duracao_dias INT                           -- Calculada na transformação
);

CREATE TABLE silver_pagamento (
    id_pagamento SERIAL PRIMARY KEY,          -- Identificador automático
    id_viagem VARCHAR(20) NOT NULL,            -- Viagem à qual pertence
    num_proposta VARCHAR(20),                  -- Número da proposta PCDP
    nome_orgao_pagador VARCHAR(255),           -- Nome do órgão pagador
    nome_ug_pagadora VARCHAR(255),             -- Nome da unidade gestora
    tipo_pagamento VARCHAR(50) NOT NULL,       -- Tipo de pagamento obrigatório
    valor DECIMAL(10, 2) CHECK (valor >= 0),    -- Pagamento não negativo

    FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem(id_viagem)   -- Exige uma viagem existente
);

CREATE TABLE silver_passagem (
    id_passagem SERIAL PRIMARY KEY,           -- Identificador automático
    id_viagem VARCHAR(20) NOT NULL,            -- Viagem à qual pertence
    meio_transporte VARCHAR(50),              -- Meio de transporte
    pais_origem_ida VARCHAR(60),               -- País de origem da ida
    uf_origem_ida VARCHAR(40),                 -- UF de origem da ida
    cidade_origem_ida VARCHAR(80),             -- Cidade de origem da ida
    pais_destino_ida VARCHAR(60),              -- País de destino da ida
    uf_destino_ida VARCHAR(40),                -- UF de destino da ida
    cidade_destino_ida VARCHAR(80),            -- Cidade de destino da ida
    valor_passagem DECIMAL(10, 2) CHECK (valor_passagem >= 0), -- Valor não negativo
    taxa_servico DECIMAL(10, 2) CHECK (taxa_servico >= 0),     -- Taxa não negativa
    data_emissao DATE,                        -- Data de emissão convertida

    FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem(id_viagem)   -- Exige uma viagem existente
);

CREATE TABLE silver_trecho (
    id_trecho SERIAL PRIMARY KEY,              -- Identificador automático
    id_viagem VARCHAR(20) NOT NULL,            -- Viagem à qual pertence
    sequencia_trecho INT,                     -- Posição do trecho na viagem
    origem_data DATE,                        -- Data de origem
    origem_uf VARCHAR(40),                    -- UF de origem
    origem_cidade VARCHAR(80),                -- Cidade de origem
    destino_data DATE,                       -- Data de destino
    destino_uf VARCHAR(40),                   -- UF de destino
    destino_cidade VARCHAR(80),               -- Cidade de destino
    meio_transporte VARCHAR(50),              -- Meio de transporte
    numero_diarias DECIMAL(10, 2) CHECK (numero_diarias >= 0), -- Diárias não negativas

    FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem(id_viagem),  -- Exige uma viagem existente

    UNIQUE (id_viagem, sequencia_trecho)       -- Impede sequência repetida na mesma viagem
);
