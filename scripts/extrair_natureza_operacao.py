"""
Extrai a natureza da operação das DANFs em PDF usando OCR.

Percorre todos os PDFs da pasta, executa OCR, busca a natureza da operação e salva o resultado em JSON.

Returns:
    None. Salva o resultado em um arquivo JSON.
"""
import os
import re
import json
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# Diretório raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Pasta dos PDFs
PDFS_FOLDER = os.path.join(ROOT_DIR, 'danfs')
# Palavras-chave para fallback
NATUREZA_KEYWORDS = [
    'VENDA', 'REMESSA', 'DEVOLUÇÃO', 'PROD', 'MERC', 'ADQ', 'RECEB', 'ENCOM', 'ENTREGA', 'COMBUS', 'LUBRIF', 'DEST', 'CONSUM', 'FINAL', '6102', '6656', 'IND', 'CTA', 'ORD', 'SUB', 'TRIB'
]
# Arquivo de saída
JSON_OUTPUT_FILE = os.path.join(ROOT_DIR, 'natureza_operacao.json')
# Pasta para salvar textos OCR
OCR_FOLDER = os.path.join(ROOT_DIR, 'ocr_texts')

os.makedirs(OCR_FOLDER, exist_ok=True)

def clean_natureza_operacao(text):
    """
    Limpa e normaliza o texto da natureza da operação.

    Args:
        text (str): Texto a ser limpo.

    Returns:
        str: Texto limpo e normalizado.
    """
    cleaned = re.sub(r'[^\w\s\-\./]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def extract_natureza_operacao_pdf_ocr(pdf_path, filename):
    """
    Extrai a natureza da operação de um arquivo PDF usando OCR.

    Args:
        pdf_path (str): Caminho do arquivo PDF.
        filename (str): Nome do arquivo PDF para salvar texto OCR se necessário.

    Returns:
        str or None: Natureza da operação extraída, ou None se não encontrada.
    """
    ocr_texts = []
    rotations = [0, 90, 180, 270]
    natureza_encontrada = None
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
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if 'NATUREZA DA OPERAÇÃO' in line.upper():
                        for j in range(i+1, len(lines)):
                            next_line = clean_natureza_operacao(lines[j])
                            if next_line and not next_line.isdigit() and len(next_line) > 5:
                                return next_line
                for line in lines:
                    line_clean = clean_natureza_operacao(line.upper())
                    if (
                        len(line_clean) > 10 and
                        not line_clean.startswith('PROTOCOLO') and
                        any(kw in line_clean for kw in NATUREZA_KEYWORDS)
                    ):
                        if not natureza_encontrada:
                            natureza_encontrada = line_clean
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
    with open(os.path.join(OCR_FOLDER, filename + '_natureza.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ocr_texts))
    return natureza_encontrada

def main():
    """
    Processa todos os PDFs na pasta especificada, extraindo a natureza da operação de cada nota fiscal.
    Salva o resultado em um arquivo JSON e os textos OCR para análise posterior.

    Returns:
        list: Lista de dicionários com os resultados extraídos.
    """
    result = []
    for filename in os.listdir(PDFS_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDFS_FOLDER, filename)
            natureza = extract_natureza_operacao_pdf_ocr(pdf_path, filename)
            if natureza:
                result.append({
                    "file": filename,
                    "natureza_operacao": natureza
                })
            else:
                print(f"Não foi possível extrair a natureza da operação de {filename}")
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'Natureza da operação extraída salva em {JSON_OUTPUT_FILE}')
    print(f'Textos OCR salvos em {OCR_FOLDER}/ para todos os arquivos.')
    return result

if __name__ == '__main__':
    main() 