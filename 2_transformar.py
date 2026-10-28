"""
2_transformar.py
----------------
Transforma as quatro tabelas Raw e carrega a camada Silver.

Regras:
- Campos vazios tornam-se NULL.
- Zero informado permanece zero.
- Custo total = diárias + passagens + outros gastos - devolução.
- Componente monetário ausente resulta em custo total NULL.
- Duração = data final - data inicial, sem acrescentar um dia.
- Data ausente resulta em duração NULL.
- Remove somente duplicatas exatas da linha Raw inteira.
- Preserva todas as tabelas Raw.
"""

from datetime import datetime  # Importa a ferramenta que interpreta datas
from decimal import Decimal, InvalidOperation  # Importa o tipo decimal e seu erro

from psycopg2 import sql  # Permite montar comandos SQL com identificadores seguros
from psycopg2.extras import DictCursor, execute_values  # Lê por nome e insere lotes

from banco import conectar  # Importa a função de conexão fornecida pelo professor
from config import TAMANHO_BLOCO  # Importa a quantidade de registros por bloco


MODELOS = (  # Define as quatro cargas na ordem em que serão realizadas
    {  # Inicia o mapeamento das viagens
        "raw": "raw_viagem",  # Define a tabela de origem
        "silver": "silver_viagem",  # Define a tabela de destino
        "colunas": (  # Define a ordem dos campos no INSERT
            "id_viagem",  # Identificador da viagem
            "num_proposta",  # Número da proposta PCDP
            "situacao",  # Situação da viagem
            "viagem_urgente",  # Indicação de urgência
            "cod_orgao_superior",  # Código do órgão superior
            "nome_orgao_superior",  # Nome do órgão superior
            "nome_viajante",  # Nome do viajante
            "cargo",  # Cargo do viajante
            "data_inicio",  # Data inicial convertida
            "data_fim",  # Data final convertida
            "destinos",  # Destinos informados
            "motivo",  # Motivo da viagem
            "valor_diarias",  # Valor decimal das diárias
            "valor_passagens",  # Valor decimal das passagens
            "valor_devolucao",  # Valor decimal devolvido
            "valor_outros_gastos",  # Valor decimal dos demais gastos
            "valor_total",  # Custo líquido calculado
            "duracao_dias",  # Diferença calculada entre as datas
        ),  # Encerra as colunas da tabela de viagens
    },  # Encerra o mapeamento das viagens
    {  # Inicia o mapeamento dos pagamentos
        "raw": "raw_pagamento",  # Define a tabela de origem
        "silver": "silver_pagamento",  # Define a tabela de destino
        "colunas": (  # Lista os campos; o banco gera id_pagamento
            "id_viagem",  # Identifica a viagem relacionada
            "num_proposta",  # Número da proposta PCDP
            "nome_orgao_pagador",  # Nome do órgão pagador
            "nome_ug_pagadora",  # Nome da unidade gestora pagadora
            "tipo_pagamento",  # Tipo de pagamento
            "valor",  # Valor decimal do pagamento
        ),  # Encerra as colunas da tabela de pagamentos
    },  # Encerra o mapeamento dos pagamentos
    {  # Inicia o mapeamento das passagens
        "raw": "raw_passagem",  # Define a tabela de origem
        "silver": "silver_passagem",  # Define a tabela de destino
        "colunas": (  # Lista os campos; o banco gera id_passagem
            "id_viagem",  # Identifica a viagem relacionada
            "meio_transporte",  # Meio de transporte utilizado
            "pais_origem_ida",  # País de origem da ida
            "uf_origem_ida",  # UF de origem da ida
            "cidade_origem_ida",  # Cidade de origem da ida
            "pais_destino_ida",  # País de destino da ida
            "uf_destino_ida",  # UF de destino da ida
            "cidade_destino_ida",  # Cidade de destino da ida
            "valor_passagem",  # Valor decimal da passagem
            "taxa_servico",  # Valor decimal da taxa de serviço
            "data_emissao",  # Data de emissão convertida
        ),  # Encerra as colunas da tabela de passagens
    },  # Encerra o mapeamento das passagens
    {  # Inicia o mapeamento dos trechos
        "raw": "raw_trecho",  # Define a tabela de origem
        "silver": "silver_trecho",  # Define a tabela de destino
        "colunas": (  # Lista os campos; o banco gera id_trecho
            "id_viagem",  # Identifica a viagem relacionada
            "sequencia_trecho",  # Posição do trecho na viagem
            "origem_data",  # Data de origem convertida
            "origem_uf",  # UF de origem
            "origem_cidade",  # Cidade de origem
            "destino_data",  # Data de destino convertida
            "destino_uf",  # UF de destino
            "destino_cidade",  # Cidade de destino
            "meio_transporte",  # Meio de transporte utilizado
            "numero_diarias",  # Número decimal de diárias
        ),  # Encerra as colunas da tabela de trechos
    },  # Encerra o mapeamento dos trechos
)  # Encerra a definição das quatro cargas


CAMPOS_DECIMAIS = {  # Agrupa os campos que precisam virar Decimal
    "valor_diarias",  # Diárias da viagem
    "valor_passagens",  # Passagens da viagem
    "valor_devolucao",  # Valor devolvido
    "valor_outros_gastos",  # Demais gastos da viagem
    "valor",  # Valor do pagamento
    "valor_passagem",  # Valor de uma passagem
    "taxa_servico",  # Taxa de serviço da passagem
    "numero_diarias",  # Quantidade de diárias do trecho
}  # Encerra o conjunto de campos decimais


CAMPOS_DATAS = {  # Agrupa os campos que precisam virar date
    "data_inicio",  # Data inicial da viagem
    "data_fim",  # Data final da viagem
    "data_emissao",  # Data de emissão da passagem
    "origem_data",  # Data de origem do trecho
    "destino_data",  # Data de destino do trecho
}  # Encerra o conjunto de campos de data


def converter_texto(valor):  # Recebe um campo textual da Raw
    """Remove espaços das extremidades e transforma vazio em None."""

    if valor is None:  # Verifica se o valor já está ausente
        return None  # Preserva a ausência

    texto = valor.strip()  # Remove espaços do início e do final
    return texto if texto else None  # Devolve o texto ou None se ficou vazio


def converter_decimal(valor):  # Recebe um campo que deve virar número decimal
    """Converte texto no formato brasileiro para Decimal."""

    texto = converter_texto(valor)  # Trata espaços e campos vazios

    if texto is None:  # Verifica se não há valor informado
        return None  # Mantém ausência sem substituir por zero

    texto = texto.replace(".", "")  # Exemplo: "1.272,97" vira "1272,97"
    texto = texto.replace(",", ".")  # Exemplo: "1272,97" vira "1272.97"

    try:  # Inicia a tentativa de conversão
        numero = Decimal(texto)  # Converte sem usar float

    except InvalidOperation as erro:  # Captura um formato numérico inválido
        raise ValueError(  # Cria uma mensagem explicativa
            f"Valor decimal inválido: {valor!r}"  # Mostra o valor original
        ) from erro  # Preserva a causa original do erro

    if not numero.is_finite():  # Detecta valores especiais como NaN e infinito
        raise ValueError(f"Valor decimal inválido: {valor!r}")  # Recusa esses valores

    return numero  # Devolve o número decimal convertido


def converter_data(valor):  # Recebe uma data no formato original do CSV
    """Converte texto DD/MM/AAAA para date."""

    texto = converter_texto(valor)  # Trata espaços e campos vazios

    if texto is None:  # Verifica se não há data informada
        return None  # Mantém ausência de data

    try:  # Inicia a tentativa de conversão
        return datetime.strptime(  # Interpreta o texto conforme o formato indicado
            texto, "%d/%m/%Y"  # Define dia com dois dígitos, mês e ano completo
        ).date()  # Devolve apenas a data, sem horário

    except ValueError as erro:  # Captura formato incorreto ou data inexistente
        raise ValueError(  # Cria uma mensagem explicativa
            f"Data inválida: {valor!r}"  # Mostra o valor original
        ) from erro  # Preserva a causa original do erro


def transformar_linha(linha, modelo):  # Recebe uma linha Raw e seu mapeamento
    """Converte os campos usados na Silver e calcula os campos da viagem."""

    dados = {}  # Guarda os valores preparados para a Silver

    for campo in modelo["colunas"]:  # Percorre os nomes das colunas de destino
        if campo in {"valor_total", "duracao_dias"}:  # Identifica campos calculados
            continue  # Deixa esses campos para os cálculos abaixo

        valor = linha[campo]  # Busca o conteúdo da coluna na linha Raw

        try:  # Inicia a conversão do campo atual
            if campo in CAMPOS_DECIMAIS:  # Verifica se o campo é decimal
                dados[campo] = converter_decimal(valor)  # Converte para Decimal

            elif campo in CAMPOS_DATAS:  # Verifica se o campo é uma data
                dados[campo] = converter_data(valor)  # Converte para date

            elif campo == "sequencia_trecho":  # Identifica o campo inteiro
                texto = converter_texto(valor)  # Trata espaços e ausência
                dados[campo] = int(texto) if texto is not None else None  # Converte se preenchido

            else:  # Trata os campos que permanecem textuais
                dados[campo] = converter_texto(valor)  # Normaliza espaços e vazio

        except ValueError as erro:  # Captura um problema de conversão
            raise ValueError(  # Acrescenta informações para localizar o problema
                f"{modelo['raw']} | viagem {linha['id_viagem']} | "  # Identifica a origem
                f"campo {campo}: {erro}"  # Identifica o campo e a falha
            ) from erro  # Preserva a causa sem descartar a linha

    if modelo["silver"] == "silver_viagem":  # Calcula os campos exclusivos da viagem
        componentes = (  # Reúne os valores necessários para calcular o custo
            dados["valor_diarias"],  # Primeiro componente: diárias
            dados["valor_passagens"],  # Segundo componente: passagens
            dados["valor_outros_gastos"],  # Terceiro componente: demais gastos
            dados["valor_devolucao"],  # Quarto componente: devolução
        )  # Encerra a reunião dos componentes

        if any(valor is None for valor in componentes):  # Detecta algum valor ausente
            dados["valor_total"] = None  # Mantém custo desconhecido como NULL

        else:  # Calcula somente quando todos os componentes estão informados
            dados["valor_total"] = (  # Inicia o cálculo do custo líquido
                dados["valor_diarias"]  # Considera as diárias
                + dados["valor_passagens"]  # Soma as passagens
                + dados["valor_outros_gastos"]  # Soma os demais gastos
                - dados["valor_devolucao"]  # Desconta o valor devolvido
            )  # Guarda o resultado como Decimal

        inicio = dados["data_inicio"]  # Obtém a data inicial convertida
        fim = dados["data_fim"]  # Obtém a data final convertida

        if inicio is None or fim is None:  # Verifica se falta alguma data
            dados["duracao_dias"] = None  # Mantém a duração desconhecida como NULL

        else:  # Calcula quando as duas datas estão disponíveis
            dados["duracao_dias"] = (fim - inicio).days  # Datas iguais resultam em zero

    return tuple(  # Prepara uma tupla com os valores da linha transformada
        dados[campo] for campo in modelo["colunas"]  # Segue a ordem definida no modelo
    )  # Devolve a tupla para a inserção no banco


def carregar_tabela(conexao, modelo):  # Recebe a conexão e o mapeamento da tabela
    """Lê uma Raw sem duplicatas exatas e prepara sua tabela Silver."""

    consulta = sql.SQL("SELECT DISTINCT * FROM {}").format(  # Remove duplicatas da linha inteira
        sql.Identifier(modelo["raw"])  # Insere o nome da tabela Raw com segurança
    )  # Finaliza o comando de leitura

    comando_insert = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(  # Define o INSERT
        sql.Identifier(modelo["silver"]),  # Insere o nome da tabela Silver
        sql.SQL(", ").join(  # Separa os nomes das colunas por vírgulas
            sql.Identifier(campo) for campo in modelo["colunas"]  # Protege cada nome
        ),  # Finaliza a lista explícita das colunas
    )  # Finaliza o comando de inserção

    total = 0  # Inicia o contador de registros preparados

    with conexao.cursor() as escrita:  # Abre e fecha automaticamente o cursor de escrita
        with conexao.cursor(  # Abre um cursor para leitura em blocos no servidor
            name=f"leitura_{modelo['raw']}",  # Dá um nome ao cursor de leitura
            cursor_factory=DictCursor,  # Permite acessar os campos pelos nomes
        ) as leitura:  # Fecha o cursor de leitura automaticamente ao sair
            leitura.execute(consulta)  # Consulta a Raw sem alterar seu conteúdo

            while True:  # Continua até terminar a leitura
                bloco = leitura.fetchmany(TAMANHO_BLOCO)  # Busca o próximo bloco

                if not bloco:  # Verifica se não há mais registros
                    break  # Encerra a repetição

                linhas = [  # Cria a lista de registros convertidos
                    transformar_linha(linha, modelo) for linha in bloco  # Converte cada linha
                ]  # Finaliza o bloco preparado para inserção

                execute_values(  # Insere vários registros por comando SQL
                    escrita,  # Usa o cursor de escrita
                    comando_insert,  # Usa o INSERT montado acima
                    linhas,  # Envia os registros convertidos
                    page_size=1000,  # Insere até mil registros por comando
                )  # Finaliza a inserção sem confirmar a transação ainda

                total += len(linhas)  # Soma os registros preparados no bloco
                print(  # Mostra o andamento da carga
                    f"{modelo['silver']}: {total:,} registros preparados."  # Informa tabela e total
                )  # A confirmação definitiva ocorrerá ao final das quatro tabelas

    return total  # Devolve o total preparado para essa tabela


def main():  # Define a função que coordena toda a transformação
    """Recarrega as quatro tabelas Silver em uma única transação."""

    conexao = conectar()  # Abre a conexão com o banco transparencia
    tabela_atual = "limpeza da Silver"  # Identifica a etapa para mensagens de erro

    try:  # Inicia a operação que será confirmada ou desfeita por inteiro
        with conexao.cursor() as cursor:  # Abre um cursor para limpar os destinos
            cursor.execute(  # Envia o comando de limpeza ao PostgreSQL
                """
                -- Esvazia todas as tabelas Silver na mesma operação.
                TRUNCATE TABLE
                    silver_pagamento,  -- Remove os pagamentos anteriores
                    silver_passagem,   -- Remove as passagens anteriores
                    silver_trecho,     -- Remove os trechos anteriores
                    silver_viagem      -- Remove as viagens anteriores
                RESTART IDENTITY       -- Reinicia os identificadores automáticos
                """
            )  # A limpeza também será desfeita se ocorrer uma falha nesta transação

        totais = {}  # Guarda a quantidade de registros de cada tabela

        for modelo in MODELOS:  # Carrega viagens antes das tabelas dependentes
            tabela_atual = modelo["silver"]  # Identifica a tabela em processamento
            totais[tabela_atual] = carregar_tabela(  # Executa e guarda o total da carga
                conexao, modelo  # Fornece a conexão e o mapeamento da tabela
            )  # O banco aplica PK, FK e demais constraints durante a inserção

        conexao.commit()  # Confirma as quatro cargas juntas no PostgreSQL
        print("\nTransformação concluída e confirmada no PostgreSQL.")  # Informa sucesso

        for tabela, total in totais.items():  # Percorre os totais confirmados
            print(f"{tabela}: {total:,} registros.")  # Exibe o resumo de cada tabela

    except Exception:  # Captura erros de conversão, consulta ou integridade
        conexao.rollback()  # Desfaz toda esta execução, inclusive o TRUNCATE
        print(f"Falha em {tabela_atual}. A execução foi desfeita.")  # Identifica a etapa
        raise  # Mostra o erro original e interrompe o script

    finally:  # Executa tanto no sucesso quanto na falha
        conexao.close()  # Fecha a conexão com o PostgreSQL


if __name__ == "__main__":  # Executa somente quando o arquivo é chamado diretamente
    main()  # Inicia a transformação completa
