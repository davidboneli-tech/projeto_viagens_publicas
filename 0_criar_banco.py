"""
0_criar_banco.py
---------------
Executa o arquivo SQL para criar o banco e as oito tabelas.
"""

import psycopg2  # Biblioteca de conexão com o PostgreSQL

from banco import conectar  # Função que conecta ao banco definido no .env
from config import PASTA_RAIZ, POSTGRES_CONFIG  # Caminho e configurações


arquivo_sql = PASTA_RAIZ / "0_criar_banco.sql"  # Localiza o arquivo SQL
conteudo_sql = arquivo_sql.read_text(encoding="utf-8")  # Lê seu conteúdo

# Separa o primeiro comando (CREATE DATABASE) dos comandos das tabelas.
sql_banco, separador, sql_tabelas = conteudo_sql.partition(";")

if not separador or not sql_tabelas.strip():  # Confere se há comandos das tabelas
    raise ValueError("O SQL precisa conter a criação do banco e das tabelas.")

config_admin = POSTGRES_CONFIG.copy()  # Copia as configurações originais
config_admin["dbname"] = "postgres"  # Seleciona um banco existente no servidor

conexao_admin = psycopg2.connect(**config_admin)  # Abre a conexão administrativa

try:
    conexao_admin.autocommit = True  # Permite executar CREATE DATABASE

    with conexao_admin.cursor() as cursor:  # Abre o cursor e o fecha ao sair
        cursor.execute(sql_banco)  # Cria o banco transparencia

    print("Banco transparencia criado.")  # Informa a conclusão desta etapa

finally:
    conexao_admin.close()  # Fecha a conexão administrativa


conexao = conectar()  # Conecta ao banco transparencia recém-criado

try:
    with conexao.cursor() as cursor:  # Abre o cursor e o fecha ao sair
        cursor.execute(sql_tabelas)  # Cria as quatro tabelas Raw e quatro Silver

    conexao.commit()  # Confirma a criação das oito tabelas
    print("As oito tabelas foram criadas com sucesso.")  # Informa o resultado

except Exception:
    conexao.rollback()  # Desfaz a criação das tabelas se ocorrer uma falha
    raise  # Mostra o erro original no terminal

finally:
    conexao.close()  # Fecha a conexão mesmo se ocorrer um erro
