import os
import re
import json
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFS_FOLDER = os.path.join(ROOT_DIR, 'danfs')
JSON_OUTPUT_FILE = os.path.join(ROOT_DIR, 'remetentes_cnpj.json')

CNPJ_REGEX = r'\d{2}\.\d{3}\.\d{3}/\d{4}[- ]?\d{2}'
CPF_REGEX = r'\d{3}\.\d{3}\.\d{3}-\d{2}'

# Função para extrair todos os CNPJs/CPFs válidos do texto OCR
def extrair_cpf_cnpj(texto):
    cnpj_match = re.search(CNPJ_REGEX, texto)
    if cnpj_match:
        return cnpj_match.group(0).replace(' ', '-')
    cpf_match = re.search(CPF_REGEX, texto)
    if cpf_match:
        return cpf_match.group(0)
    return None

def extrair_razao_social(texto, cnpj):
    linhas = texto.splitlines()
    blacklist = [
        'NOME / RAZÃO SOCIAL', 'NOME/RAZÃO SOCIAL', 'CNPJ', 'DATA EMISSÃO', 'DATA DA EMISSÃO',
        'DESTINATÁRIO', 'REMETENTE', 'CPF', 'ENDEREÇO', 'BAIRRO', 'CEP', 'UF', 'INSCRIÇÃO',
        'FATURA', 'CÁLCULO', 'TRANSPORTADOR', 'DADOS', 'INFORMAÇÕES', 'COMPLEMENTARES', 'RESERVADO', 'FISCO'
    ]
    keywords = ['Ltda', 'ME', 'EPP', 'S/A', 'Indústria', 'Comércio', 'COOP', 'ASSOCIAÇÃO', 'SOCIEDADE', 'EMPRESA', 'LTDA', 'S.A.', 'INDUSTRIAL', 'INDÚSTRIA']
    # 1. Procurar após bloco DESTINATÁRIO/REMETENTE
    for i, linha in enumerate(linhas):
        if 'RECEBEMOS DE' in linha.upper():
            # Extrai nome da empresa entre 'RECEBEMOS DE' e o próximo ponto, hífen ou termo genérico
            after = linha.upper().split('RECEBEMOS DE', 1)[1]
            # Remove tudo após ponto, hífen ou 'OS PRODUTOS', 'CONSTANTES', etc
            after = after.split(' OS PRODUTOS')[0].split(' CONSTANTES')[0].split('.')[0].split('-')[0]
            # Remove espaços extras e retorna
            nome = after.strip().title()
            # Se contiver palavra-chave típica, retorna
            if any(kw.lower() in nome.lower() for kw in keywords):
                return nome
        if 'DESTINATÁRIO/REMETENTE' in linha.upper() or 'REMETENTE' in linha.upper():
            for j in range(i+1, min(i+6, len(linhas))):
                l = linhas[j].strip()
                if l and not any(b.lower() in l.lower() for b in blacklist) and not re.search(CNPJ_REGEX, l) and len(l) > 3:
                    for kw in keywords:
                        if kw.lower() in l.lower():
                            return l
    # 2. Procurar por palavras-chave típicas de razão social, ignorando blacklist
    for linha in linhas:
        if not any(b.lower() in linha.lower() for b in blacklist):
            for kw in keywords:
                if kw.lower() in linha.lower():
                    return linha.strip()
    # 3. Procurar linha anterior ao CNPJ (fallback), ignorando blacklist
    for i, linha in enumerate(linhas):
        if cnpj and cnpj.replace('-', ' ').replace('/', '/').replace('.', '.') in linha.replace('-', ' ').replace('/', '/').replace('.', '.'):
            for j in range(i-1, -1, -1):
                l = linhas[j].strip()
                if l and len(l) > 3 and not re.search(CNPJ_REGEX, l) and not any(b.lower() in l.lower() for b in blacklist):
                    for kw in keywords:
                        if kw.lower() in l.lower():
                            return l
    return None

def ocr_pdf(pdf_path):
    texto_ocr = []
    rotations = [0, 90, 180, 270]
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        for idx, page in enumerate(pages):
            for rot in rotations:
                if rot == 0:
                    img = page
                else:
                    img = page.rotate(rot, expand=True)
                text = pytesseract.image_to_string(img, lang='por')
                texto_ocr.append(text)
    except Exception as e:
        print(f"Erro ao processar {pdf_path}: {e}")
    return '\n'.join(texto_ocr)

def main():
    resultados = []
    for filename in os.listdir(PDFS_FOLDER):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(PDFS_FOLDER, filename)
            texto = ocr_pdf(pdf_path)
            cnpj = extrair_cpf_cnpj(texto)
            razao_social = extrair_razao_social(texto, cnpj) if cnpj else None
            resultados.append({
                "file": filename,
                "cpf_or_cnpj": cnpj,
                "razao_social": razao_social
            })
    with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f'Resultado salvo em {JSON_OUTPUT_FILE}')

if __name__ == '__main__':
    main() 