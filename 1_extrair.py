"""
1_extrair.py
------------
Baixa o ZIP, lê os quatro CSVs em blocos e carrega as tabelas Raw.
Mantém os valores originais, sem limpeza ou conversão de tipos.
"""

import csv  # Lê os campos dos arquivos CSV
from io import TextIOWrapper  # Converte os bytes do ZIP em texto
from itertools import islice  # Limita a quantidade de registros por bloco
from zipfile import ZipFile  # Abre o ZIP sem extrair os arquivos no disco

import gdown  # Permite baixar arquivos do Google Drive
from psycopg2 import sql  # Monta comandos SQL com nomes de tabelas seguros

from banco import conectar, executar, inserir_em_lote  # Funções do professor
from config import (
    ARQUIVOS,         # Relaciona cada CSV à sua tabela Raw
    CSV_ENCODING,     # Codificação dos CSVs: latin-1
    CSV_SEPARADOR,    # Separador dos campos: ponto e vírgula
    DRIVE_FILE_ID,    # Identificador do ZIP no Google Drive
    PASTA_DADOS,      # Caminho da pasta data
    TAMANHO_BLOCO,    # Quantidade máxima de registros por bloco
)


def baixar_zip():
    """Baixa o ZIP e retorna o caminho do arquivo."""

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)  # Cria data se não existir

    arquivo_zip = PASTA_DADOS / "viagens_2025_6meses.zip"  # Define o destino

    resultado = gdown.download(
        id=DRIVE_FILE_ID,          # Identifica o arquivo no Google Drive
        output=str(arquivo_zip),   # Informa onde salvar o ZIP
        quiet=False,              # Mostra o progresso do download
    )

    if resultado is None:  # Verifica se o download não retornou um caminho
        raise RuntimeError("Não foi possível baixar o ZIP do Google Drive.")

    return arquivo_zip  # Entrega o caminho para as próximas etapas


def ler_blocos(arquivo_zip, nome_csv):
    """Lê um CSV dentro do ZIP e entrega seus registros em blocos."""

    with ZipFile(arquivo_zip, "r") as zip_aberto:  # Abre o ZIP para leitura
        with zip_aberto.open(nome_csv) as arquivo_binario:  # Abre o CSV
            with TextIOWrapper(
                arquivo_binario,
                encoding=CSV_ENCODING,  # Interpreta os caracteres usando latin-1
                newline="",  # Deixa o leitor CSV interpretar as quebras de linha
            ) as arquivo_texto: # deixa o leitor CSV interpretar as quebras de linha

                leitor = csv.reader( # Cria um leitor CSV para iterar sobre os registros
                    arquivo_texto, # Arquivo de texto do CSV
                    delimiter=CSV_SEPARADOR,  # Usa ponto e vírgula como separador
                )

                next(leitor)  # Pula a primeira linha, que contém o cabeçalho

                while True:  # Repete a leitura até terminar o CSV
                    bloco = list(islice(leitor, TAMANHO_BLOCO))  # Lê um bloco

                    if not bloco:  # Se não houver mais registros, encerra
                        break

                    yield bloco  # Entrega o bloco e pausa até pedirem o próximo


def carregar_raw(conexao, arquivo_zip, nome_csv, tabela): # carrega os registros de um CSV para a tabela Raw correspondente
    """Esvazia a tabela Raw e insere os registros do CSV correspondente."""

    comando_truncate = sql.SQL("TRUNCATE TABLE {}").format( # assegura que a tabela Raw esteja vazia antes de inserir novos registros
        sql.Identifier(tabela),  # Identifica a tabela que será esvaziada
    )

    executar(conexao, comando_truncate)  # Remove os dados da carga anterior
    total = 0  # Inicia a contagem dos registros inseridos

    for bloco in ler_blocos(arquivo_zip, nome_csv):  # Recebe um bloco por vez
        marcadores = sql.SQL(", ").join(
            sql.Placeholder() for _ in bloco[0]  # Cria um %s por campo do CSV
        )

        comando_insert = sql.SQL("INSERT INTO {} VALUES ({})").format(
            sql.Identifier(tabela),  # Define a tabela de destino
            marcadores,  # Define onde entrarão os valores de cada registro
        )

        inserir_em_lote(conexao, comando_insert, bloco)  # Insere e confirma o bloco
        total += len(bloco)  # Soma a quantidade de registros inseridos

        print(f"{tabela}: {total:,} registros carregados.")  # Mostra o progresso

    print(f"Carga de {tabela} concluída: {total:,} registros.")  # Mostra o total


def main():
    """Coordena o download e a carga das quatro tabelas Raw."""

    conexao = None  # Indica que a conexão ainda não foi aberta

    try:
        arquivo_zip = baixar_zip()  # Baixa o ZIP do Google Drive

        with ZipFile(arquivo_zip, "r") as zip_aberto:  # Abre o ZIP para conferência
            nomes = zip_aberto.namelist()  # Lista os arquivos disponíveis

            for dados in ARQUIVOS.values():  # Percorre os CSVs do config.py
                if dados["csv"] not in nomes:  # Confere se o CSV está no ZIP
                    raise FileNotFoundError(
                        f"CSV não encontrado no ZIP: {dados['csv']}"
                    )

        conexao = conectar()  # Abre a conexão com o banco transparencia

        for dados in ARQUIVOS.values():  # Percorre os quatro arquivos configurados
            carregar_raw(
                conexao,               # Conexão com o PostgreSQL
                arquivo_zip,           # Caminho do ZIP baixado
                dados["csv"],          # Nome do CSV de origem
                dados["tabela_raw"],   # Nome da tabela Raw de destino
            )

        print("Carga das quatro tabelas Raw concluída com sucesso.")

    except Exception:
        if conexao is not None:  # Verifica se a conexão chegou a ser aberta
            conexao.rollback()  # Desfaz operações ainda não confirmadas

        print("Falha na extração ou carga. Veja o erro abaixo.")
        raise  # Exibe o erro original no terminal

    finally:
        if conexao is not None:  # Verifica se existe uma conexão aberta
            conexao.close()  # Fecha a conexão mesmo se ocorrer uma falha


if __name__ == "__main__":
    main()  # Inicia o processo ao executar este arquivo diretamente
