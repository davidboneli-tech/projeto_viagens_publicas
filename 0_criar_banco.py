"""
0_criar_banco.py
---------------
Recria o banco e executa a criação das oito tabelas.
ATENÇÃO: a execução apaga todos os dados anteriores do banco transparencia.
"""

import psycopg2  # Conecta ao PostgreSQL

from banco import conectar  # Abre a conexão com o banco do projeto
from config import PASTA_RAIZ, POSTGRES_CONFIG  # Importa caminho e configuração


def main():  # Organiza a recriação do banco e das tabelas
    if POSTGRES_CONFIG["dbname"] != "transparencia":  # Confere o banco esperado pelo SQL
        raise ValueError("POSTGRES_DATABASE deve ser transparencia neste projeto.")

    arquivo_sql = PASTA_RAIZ / "0_criar_banco.sql"  # Localiza o SQL
    conteudo_sql = arquivo_sql.read_text(encoding="utf-8")  # Lê os comandos
    partes = conteudo_sql.split(";", 2)  # Separa DROP, CREATE DATABASE e tabelas

    if len(partes) != 3 or not partes[2].strip():  # Confere as três partes
        raise ValueError("O SQL deve conter DROP DATABASE, CREATE DATABASE e as tabelas.")

    sql_drop, sql_create, sql_tabelas = partes  # Identifica cada etapa
    config_admin = POSTGRES_CONFIG.copy()  # Copia as configurações
    config_admin["dbname"] = "postgres"  # Conecta a um banco administrativo

    conexao_admin = psycopg2.connect(**config_admin)  # Abre a conexão administrativa
    try:  # Garante o fechamento da conexão
        conexao_admin.autocommit = True  # Executa DROP e CREATE fora de transação
        with conexao_admin.cursor() as cursor:  # Fecha o cursor ao terminar
            cursor.execute(sql_drop)  # Apaga transparencia, caso exista
            cursor.execute(sql_create)  # Cria novamente o banco vazio
        print("Banco transparencia recriado.")  # Informa a conclusão
    finally:  # Executa mesmo se ocorrer uma falha
        conexao_admin.close()  # Fecha a conexão administrativa

    conexao = conectar()  # Conecta ao banco recém-criado
    try:  # Inicia a criação das tabelas
        with conexao.cursor() as cursor:  # Fecha o cursor ao terminar
            cursor.execute(sql_tabelas)  # Cria as quatro Raw e quatro Silver
        conexao.commit()  # Confirma a criação das oito tabelas
        print("As oito tabelas foram criadas com sucesso.")  # Informa o resultado
    except Exception:  # Captura uma falha na criação das tabelas
        conexao.rollback()  # Desfaz a criação incompleta das tabelas
        raise  # Exibe o erro original
    finally:  # Executa no sucesso ou na falha
        conexao.close()  # Fecha a conexão com o projeto


if __name__ == "__main__":  # Executa apenas quando chamado diretamente
    main()  # Inicia a recriação
