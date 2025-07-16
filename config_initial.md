# Extração de Dados de DANFs via OCR

Este projeto realiza a extração de informações de DANFs em formato PDF utilizando OCR (Reconhecimento Óptico de Caracteres). Os dados extraídos incluem:

- Chave de acesso
- Natureza da operação
- Número e série da nota
- CNPJ ou CPF e razão social do remetente

---

# ⚙️ Configuração do Projeto

## 📦 Como configurar o ambiente Python 
Crie um ambiente virtual


<code>python -m venv venv</code>

## Ative o ambiente virtual

### Linux/macOS
<code>source venv/bin/activate</code>

### Windows
<code>.venv\Scripts\activate</code>

## Instale as dependências


<code>pip install -r requirements.txt</code>

Certifique-se de que o Tesseract e o Poppler estão instalados no sistema:

###  🐧 Ubuntu/Debian

<code>sudo apt install tesseract-ocr poppler-utils</code>

## Execute o código

<code>python main.py</code>