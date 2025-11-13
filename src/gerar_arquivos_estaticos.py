import os

#Classe para cores no terminal
class Cores:
    VERDE = '\033[92m'    #Verde para sucesso
    VERMELHO = '\033[91m' #Vermelho para erro
    AMARELO = '\033[93m'  #Amarelo para aviso
    AZUL = '\033[94m'     #Azul para informação
    MAGENTA = '\033[95m'  #Magenta para destaque
    CIANO = '\033[96m'    #Ciano para título
    RESET = '\033[0m'     #Reset para cor normal
    NEGRITO = '\033[1m'   #Negrito

    @staticmethod
    def sucesso(texto):
        return f"{Cores.VERDE}[OK]{Cores.RESET} {texto}"
    
    @staticmethod
    def erro(texto):
        return f"{Cores.VERMELHO}[ERRO]{Cores.RESET} {texto}"
    
    @staticmethod
    def aviso(texto):
        return f"{Cores.AMARELO}[AVISO]{Cores.RESET} {texto}"
    
    @staticmethod
    def info(texto):
        return f"{Cores.AZUL}[INFO]{Cores.RESET} {texto}"
    
    @staticmethod
    def destaque(texto):
        return f"{Cores.MAGENTA}{texto}{Cores.RESET}"
    
    @staticmethod
    def titulo(texto):
        return f"{Cores.CIANO}{Cores.NEGRITO}{texto}{Cores.RESET}"

def gerar_arquivo(caminho, tamanho_bytes, nome):
    os.makedirs(caminho, exist_ok=True)
    arquivo_completo = os.path.join(caminho, nome)
    
    #Gera conteúdo com caracteres variados
    conteudo = ""
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n"
    indice_char = 0
    
    for i in range(tamanho_bytes):
        conteudo += chars[indice_char % len(chars)]
        indice_char += 1
        if i % 80 == 79:  #Quebra de linha a cada 80 caracteres
            conteudo += "\n"
    
    with open(arquivo_completo, 'w') as f:
        f.write(conteudo)
    
    tamanho_real = os.path.getsize(arquivo_completo)
    print(Cores.sucesso(f"Criado: {nome} ({tamanho_real:,} bytes)"))


def principal():
    print("=" * 70)
    print("Gerador de Arquivos Estáticos de Teste")
    print("Trabalho de Redes II - 2025.2")
    print("=" * 70)
    print()
    
    #Diretório onde os arquivos serão criados
    diretorio_estatico = 'arquivos_estaticos'
    
    #Gerar arquivos de diferentes tamanhos
    arquivos = [
        ('pequeno-1kb.txt', 1 * 1024),           #1 KB
        ('pequeno-10kb.txt', 10 * 1024),         #10 KB
        ('pequeno-50kb.txt', 50 * 1024),         #50 KB
        ('medio-100kb.txt', 100 * 1024),         #100 KB
        ('medio-500kb.txt', 500 * 1024),         #500 KB
        ('medio-700kb.txt', 700 * 1024),         #700 KB
        ('grande-1mb.txt', 1 * 1024 * 1024),     #1 MB
        ('grande-5mb.txt', 5 * 1024 * 1024),     #5 MB
        ('grande-7mb.txt', 7 * 1024 * 1024),     #7 MB
        ('enorme-10mb.txt', 10 * 1024 * 1024),   #10 MB
        ('enorme-20mb.txt', 20 * 1024 * 1024),   #20 MB
        ('enorme-50mb.txt', 50 * 1024 * 1024),   #50 MB
        # ('enormosauro-1gb.txt', 1 * 1024 * 1024 * 1024)  #1 GB
    ]
    
    print(f"Criando arquivos em: {diretorio_estatico}/\n")
    
    for nome, tamanho in arquivos:
        gerar_arquivo(diretorio_estatico, tamanho, nome)
    
    print()
    print("=" * 70)
    print(Cores.sucesso("Todos os arquivos foram criados com sucesso!"))
    print("=" * 70)
    print()
    print(f"Total de arquivos: {len(arquivos)}")
    print(f"Tamanho total aproximado: {sum([t for _, t in arquivos]) / (1024 * 1024):.2f} MB")
    print()


if __name__ == '__main__':
    principal()
