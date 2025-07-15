"""
Extrai informações do remetente (nome, CNPJ) de um PDF de DANF usando OCR.

Executa OCR nas imagens do PDF, busca padrões de nome e CNPJ e salva o resultado em JSON.

Returns:
    None. Salva o resultado em um arquivo JSON.
"""
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import re
import json

# Caminho do PDF
pdf_path = 'danfs/7187.pdf'
output_json = 'remetente_7187.json'

def pdf_to_images(pdf_path):
    """
    Converte todas as páginas de um PDF em imagens.

    Args:
        pdf_path (str): Caminho do arquivo PDF.

    Returns:
        list: Lista de objetos PIL.Image de cada página do PDF.
    """
    images = convert_from_path(pdf_path, dpi=300)
    return images

def extrair_texto_ocr(images):
    """
    Executa OCR em uma lista de imagens.

    Args:
        images (list): Lista de objetos PIL.Image.

    Returns:
        str: Texto extraído concatenado de todas as imagens.
    """
    texto = ''
    for img in images:
        texto += pytesseract.image_to_string(img, lang='por') + '\n'
    return texto

def extrair_remetente(texto):
    """
    Extrai o nome e o CNPJ do remetente a partir do texto OCR.

    Args:
        texto (str): Texto extraído do PDF via OCR.

    Returns:
        tuple: (nome, cnpj) extraídos do texto.
    """
    # Heurística baseada no exemplo fornecido
    # Procurar CNPJ
    cnpj_match = re.search(r'CNPJ[:\s]*([0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2})', texto)
    cnpj = cnpj_match.group(1) if cnpj_match else ''

    # Procurar nome (linha antes do endereço)
    nome = ''
    linhas = texto.split('\n')
    for i, linha in enumerate(linhas):
        if 'Avenida dos Imigrantes' in linha:
            nome = linhas[i-1].strip()
            break

    return nome, cnpj

def main():
    """
    Executa o fluxo de extração do remetente do PDF e salva o resultado em JSON.

    Returns:
        None. Salva o resultado em um arquivo JSON.
    """
    images = pdf_to_images(pdf_path)
    texto = extrair_texto_ocr(images)
    print('Texto extraído pelo OCR:\n', texto)
    nome, cnpj = extrair_remetente(texto)
    resultado = {
        'file': '7187.pdf',
        'nome': nome,
        'CNPJ': cnpj,
    }
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print('Extração concluída. Veja o arquivo', output_json)

if __name__ == '__main__':
    main() 