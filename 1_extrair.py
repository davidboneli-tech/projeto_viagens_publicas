"""
1_extrair.py
------------
Download dos dados para a camada Raw.
"""

import gdown  # Permite baixar arquivos do Google Drive

from config import DRIVE_FILE_ID, PASTA_DADOS  # Importa o ID e a pasta de destino


def baixar_zip():
    """Baixa o ZIP e retorna o caminho do arquivo."""

    PASTA_DADOS.mkdir(parents=True, exist_ok=True)  # Cria data se ainda não existir

    arquivo_zip = PASTA_DADOS / "viagens_2025_6meses.zip"  # Define o destino

    resultado = gdown.download(
        id=DRIVE_FILE_ID,          # Identifica o arquivo no Google Drive
        output=str(arquivo_zip),   # Informa onde salvar o ZIP
        quiet=False,              # Mostra o progresso do download
    )

    if resultado is None:  # Verifica se o download falhou sem retornar um caminho
        raise RuntimeError("Não foi possível baixar o ZIP do Google Drive.")

    return arquivo_zip  # Devolve o caminho para a próxima etapa


if __name__ == "__main__":  # Executa este bloco ao rodar o arquivo diretamente
    try:
        caminho_zip = baixar_zip()  # Chama a função de download
        print(f"Download concluído: {caminho_zip}")  # Mostra onde o ZIP foi salvo

    except Exception:
        print("Falha na etapa de download.")  # Identifica a etapa que falhou
        raise  # Exibe o erro original no terminal
