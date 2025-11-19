import hashlib

#Matrícula e informações do aluno
MATRICULA = "20239057601"
NOME_ALUNO = "Raildom" 

#Cabeçalho HTTP personalizado
def gerar_id_personalizado():
    dados = f"{MATRICULA} {NOME_ALUNO}"
    return hashlib.md5(dados.encode()).hexdigest()

ID_CUSTOMIZADO = gerar_id_personalizado()
