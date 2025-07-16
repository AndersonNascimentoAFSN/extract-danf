"""
Extrai o número e a série das notas fiscais em PDFs usando OCR.

Percorre todos os PDFs da pasta, executa OCR, busca padrões de número e série e salva o resultado em JSON.

Returns:
    None: Salva o resultado em um arquivo JSON.
"""
import os
import re
import json
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import pytesseract

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFS_FOLDER = os.path.join(ROOT_DIR, 'danfs')
JSON_OUTPUT_FILE = os.path.join(ROOT_DIR, 'numero_serie_todos.json')
OCR_FOLDER = os.path.join(ROOT_DIR, 'ocr_texts')

os.makedirs(OCR_FOLDER, exist_ok=True)

def clean_text(text):
    """
    Limpa e normaliza o texto para facilitar a busca por número e série.

    Args:
        text (str): Texto a ser limpo.

    Returns:
        str: Texto limpo e normalizado.
    """
    cleaned = re.sub(r'[^\w\s\-\./º:]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def preprocess_image(img):
    """
    Converte a imagem para escala de cinza e aplica autocontraste para melhorar o OCR.

    Args:
        img (PIL.Image): Imagem a ser processada.

    Returns:
        PIL.Image: Imagem processada em escala de cinza e autocontraste.
    """
    gray = img.convert('L')
    binarized = ImageOps.autocontrast(gray)
    return binarized

def find_numero_after_prefix(lines):
    """
    Procura o número da nota logo após encontrar uma linha com o prefixo 'NÚMERO'.
    Tenta extrair na mesma linha ou nas próximas duas linhas.

    Args:
        lines (list): Lista de linhas do texto OCR.

    Returns:
        str or None: Número encontrado ou None se não encontrado.
    """
    for i, line in enumerate(lines):
        if re.search(r'N[ÚU]MERO', line.upper()):
            match = re.search(r'N[ÚU]MERO[\s:]*([0-9]{6,10})', line.upper())
            if match:
                return match.group(1).zfill(9)
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j]
                    match2 = re.search(r'\b([0-9]{6,10})\b', next_line)
                    if match2:
                        return match2.group(1).zfill(9)
    return None

def find_best_number(lines):
    """
    Busca a sequência numérica de 6 a 9 dígitos mais frequente no texto,
    ignorando possíveis CNPJs e chaves de acesso.

    Args:
        lines (list): Lista de linhas do texto OCR.

    Returns:
        str or None: Número mais frequente encontrado ou None se não houver candidatos.
    """
    candidates = []
    for line in lines:
        if re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', line):
            continue
        if re.search(r'\d{44}', line):
            continue
        for match in re.findall(r'\b\d{6,9}\b', line):
            candidates.append(match)
    if candidates:
        return max(set(candidates), key=candidates.count).zfill(9)
    return None

def extract_numero_serie_pdf_ocr(pdf_path, filename):
    """
    Extrai o número e a série da nota fiscal de um PDF usando OCR.
    Tenta múltiplas rotações e pré-processamento para melhorar a acurácia.
    Salva o texto OCR para análise posterior em caso de falha.

    Args:
        pdf_path (str): Caminho do arquivo PDF.
        filename (str): Nome do arquivo PDF para salvar texto OCR se necessário.

    Returns:
        tuple or None: (numero, serie) extraídos ou None se não encontrados.
    """
    ocr_texts = []
    rotations = [0, 90, 180, 270]
    numero = None
    serie = None
    try:
        pages = convert_from_path(pdf_path, dpi=600)
        for idx, page in enumerate(pages):
            for rot in rotations:
                if rot == 0:
                    img = page
                else:
                    img = page.rotate(rot, expand=True)
                img = preprocess_image(img)
                text = pytesseract.image_to_string(img, lang='por')
                ocr_texts.append(f'--- Página {idx+1} (rot {rot}°) ---\n{text}\n')
                lines = text.splitlines()
                lines_clean = [clean_text(l) for l in lines]
                if numero is None:
                    numero = find_numero_after_prefix(lines)
                for line, line_clean in zip(lines, lines_clean):
                    if numero is None:
                        match_num = re.search(r'N[ºO][\s:]*([0-9]{6,10})', line_clean)
                        if match_num:
                            numero = match_num.group(1).zfill(9)
                        match_num2 = re.search(r'N[ÚU]MERO[\s:]*([0-9]{6,10})', line_clean)
                        if match_num2:
                            numero = match_num2.group(1).zfill(9)
                    if serie is None:
                        match_serie = re.search(r'S[ÉE]RIE[\s:]*([0-9]{1,3})', line_clean)
                        if match_serie:
                            try:
                                serie = int(match_serie.group(1))
                            except Exception:
                                pass
                        if re.search(r'S[ÉE]RIE[\s:]*1', line_clean):
                            serie = 1
                # Sempre busca a sequência mais frequente de 6 a 9 dígitos
                best_num = find_best_number(lines_clean)
                if best_num:
                    numero = best_num
                if numero and serie is not None:
                    return numero, serie
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
    with open(os.path.join(OCR_FOLDER, filename + '_numero_serie.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ocr_texts))
    return numero, serie

def main():
    """
    Processa todos os PDFs na pasta especificada, extraindo número e série de cada nota fiscal.
    Salva o resultado em um arquivo JSON e os textos OCR para análise posterior.

    Returns:
        list: Lista de dicionários com os resultados extraídos.
    """
    result = []
    for filename in os.listdir(PDFS_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDFS_FOLDER, filename)
            numero, serie = extract_numero_serie_pdf_ocr(pdf_path, filename)
            if numero and serie is not None:
                result.append({
                    "file": filename,
                    "number": numero.lstrip('0'),
                    "serie": serie,
                })
            else:
                print(f"Não foi possível extrair número e/ou série de {filename}")
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'Resultado salvo em {JSON_OUTPUT_FILE}')
    if not result:
        print('Não foi possível extrair número e série de nenhum arquivo. Veja os textos OCR salvos para análise.')
    return result

if __name__ == '__main__':
    main() 