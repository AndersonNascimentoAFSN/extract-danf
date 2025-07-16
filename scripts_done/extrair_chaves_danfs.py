"""
Extrai a chave de acesso das DANFs em PDF usando OCR.

Percorre todos os PDFs da pasta, executa OCR, busca a chave de acesso e salva o resultado em JSON.

Returns:
    None. Salva o resultado em um arquivo JSON.
"""
import os
import re
import json
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# Pasta dos PDFs
PDFS_FOLDER = 'danfs'
# Regex para chave de acesso: 11 blocos de 4 dígitos separados por espaço, quebra de linha ou nada
ACCESS_KEY_REGEX = r'((?:\d{4}[ \n]?){11})'
# Arquivo de saída
JSON_OUTPUT_FILE = 'chaves_danfs.json'
# Pasta para salvar textos OCR
OCR_FOLDER = 'ocr_texts'

os.makedirs(OCR_FOLDER, exist_ok=True)

def normalize_key(key):
    """
    Remove todos os caracteres não numéricos de uma string.

    Args:
        key (str): String contendo a chave de acesso com possíveis separadores.

    Returns:
        str: String contendo apenas os dígitos da chave de acesso.
    """
    return re.sub(r'\D', '', key)

def extract_first_key_pdf_ocr(pdf_path, filename):
    """
    Extrai a primeira chave de acesso encontrada em um arquivo PDF usando OCR.

    Args:
        pdf_path (str): Caminho completo para o arquivo PDF.
        filename (str): Nome do arquivo PDF para salvar texto OCR se necessário.

    Returns:
        str or None: Chave de acesso normalizada (44 dígitos) se encontrada, None caso contrário.
    """
    ocr_texts = []
    rotations = [0, 90, 180, 270]
    try:
        pages = convert_from_path(pdf_path, dpi=600)
        for idx, page in enumerate(pages):
            for rot in rotations:
                if rot == 0:
                    img = page
                else:
                    img = page.rotate(rot, expand=True)
                text = pytesseract.image_to_string(img, lang='por')
                ocr_texts.append(f'--- Página {idx+1} (rot {rot}°) ---\n{text}\n')
                found_keys = re.findall(ACCESS_KEY_REGEX, text)
                for key in found_keys:
                    normalized_key = normalize_key(key)
                    if len(normalized_key) == 44:
                        return normalized_key
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
    with open(os.path.join(OCR_FOLDER, filename + '.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ocr_texts))
    return None

def main():
    """
    Processa todos os PDFs na pasta especificada, extrai as chaves de acesso usando OCR e salva os resultados em um arquivo JSON.
    Para arquivos onde não foi possível extrair a chave, salva o texto OCR extraído para análise posterior.

    Returns:
        list: Lista de dicionários com os resultados extraídos.
    """
    result = []
    for filename in os.listdir(PDFS_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDFS_FOLDER, filename)
            key = extract_first_key_pdf_ocr(pdf_path, filename)
            if key:
                result.append({
                    "file": filename,
                    "access_key": key
                })
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'Chaves extraídas salvas em {JSON_OUTPUT_FILE}')
    print(f'Textos OCR salvos em {OCR_FOLDER}/ para arquivos sem chave extraída.')
    return result

if __name__ == '__main__':
    main() 