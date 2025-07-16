from scripts.extrair_chaves_danfs import main as extrair_chaves
from scripts.extrair_natureza_operacao import main as extrair_natureza
from scripts.extrair_numero_serie import main as extrair_numero_serie
from scripts.extrair_remetente import main as extrair_remetente

def main():
    print('\n==> Iniciando extração de chaves de acesso')
    extrair_chaves()

    print('\n==> Iniciando extração da natureza da operação')
    extrair_natureza()

    print('\n==> Iniciando extração de número e série')
    extrair_numero_serie()

    print('\n==> Iniciando extração de remetente (CNPJ e razão social)')
    extrair_remetente()

    print('\n✅ Todos os scripts foram executados com sucesso.')

if __name__ == '__main__':
    main()
