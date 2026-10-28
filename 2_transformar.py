"""
2_transformar.py
----------------
Funções de conversão para a camada Silver.
"""

from datetime import datetime  # Importa a ferramenta que interpreta datas
from decimal import Decimal, InvalidOperation  # Importa o tipo decimal e seu erro


def converter_decimal(valor):  # Define a função e recebe o valor a converter
    """Converte um texto no formato brasileiro para Decimal."""

    if valor is None:  # Verifica se o valor recebido já está ausente
        return None  # Devolve a ausência sem tentar converter

    texto = valor.strip()  # Remove espaços do início e do final do texto

    if not texto:  # Verifica se o texto ficou vazio
        return None  # Retorna ausência; não confunde vazio com zero

    texto = texto.replace(".", "")  # Exemplo: "1.272,97" passa a "1272,97"
    texto = texto.replace(",", ".")  # Exemplo: "1272,97" passa a "1272.97"

    try:  # Inicia a tentativa de conversão
        numero = Decimal(texto)  # Transforma o texto em um número decimal exato

    except InvalidOperation as erro:  # Captura uma falha na conversão decimal
        raise ValueError(f"Valor decimal inválido: {valor!r}") from erro  # Mostra o valor e preserva a causa

    if not numero.is_finite():  # Verifica se o resultado é NaN ou infinito
        raise ValueError(f"Valor decimal inválido: {valor!r}")  # Interrompe com uma mensagem explicativa

    return numero  # Devolve o número convertido para quem chamou a função


def converter_data(valor):  # Define a função e recebe a data a converter
    """Converte um texto DD/MM/AAAA para um objeto date."""

    if valor is None:  # Verifica se o valor recebido já está ausente
        return None  # Devolve a ausência sem tentar converter

    texto = valor.strip()  # Remove espaços do início e do final do texto

    if not texto:  # Verifica se o texto ficou vazio
        return None  # Retorna ausência de data

    try:  # Inicia a tentativa de conversão
        return datetime.strptime(texto, "%d/%m/%Y").date()  # Interpreta dia/mês/ano e devolve apenas a data

    except ValueError as erro:  # Captura formato incorreto ou data inexistente
        raise ValueError(f"Data inválida: {valor!r}") from erro  # Mostra o valor e preserva a causa


if __name__ == "__main__":  # Executa os exemplos somente quando este arquivo é rodado diretamente
    print(converter_decimal("1.272,97"))  # Chama a conversão e mostra 1272.97
    print(converter_data("15/03/2025"))  # Chama a conversão e mostra 2025-03-15
