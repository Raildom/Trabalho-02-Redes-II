#Cliente HTTP para testar os servidores

import socket
import time
import json
import threading
from configuracao import ID_CUSTOMIZADO, PORTA_SERVIDOR

class ClienteHTTP:
    def __init__(self, host_servidor, porta_servidor=PORTA_SERVIDOR):
        self.host_servidor = host_servidor
        self.porta_servidor = porta_servidor
        
    def enviar_requisicao(self, metodo='GET', caminho='/', cabecalhos=None, corpo=None):
        #Envia uma requisição HTTP para o servidor
        if cabecalhos is None:
            cabecalhos = {}
        
        #Adiciona o cabeçalho customizado obrigatório
        cabecalhos['X-Custom-ID'] = ID_CUSTOMIZADO
        cabecalhos['Host'] = f"{self.host_servidor}:{self.porta_servidor}"
        cabecalhos['Connection'] = 'close'
        
        try:
            #Cria conexão
            socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_cliente.settimeout(10)  #Timeout de 10 segundos
            
            tempo_inicio = time.time()
            socket_cliente.connect((self.host_servidor, self.porta_servidor))
            tempo_conexao = time.time() - tempo_inicio
            
            #Monta a requisição HTTP
            linha_requisicao = f"{metodo} {caminho} HTTP/1.1\r\n"
            linhas_cabecalho = "\r\n".join([f"{chave}: {valor}" for chave, valor in cabecalhos.items()])
            
            if corpo:
                cabecalhos['Content-Length'] = str(len(corpo))
                requisicao = f"{linha_requisicao}{linhas_cabecalho}\r\n\r\n{corpo}"
            else:
                requisicao = f"{linha_requisicao}{linhas_cabecalho}\r\n\r\n"
            
            #Envia requisição
            inicio_envio = time.time()
            socket_cliente.send(requisicao.encode('utf-8'))
            tempo_envio = time.time() - inicio_envio
            
            #Recebe resposta
            inicio_recepcao = time.time()
            dados_resposta = b""
            while True:
                pedaco = socket_cliente.recv(4096)
                if not pedaco:
                    break
                dados_resposta += pedaco
                
                #Verifica se recebeu a resposta completa
                if b"\r\n\r\n" in dados_resposta:
                    fim_cabecalho = dados_resposta.find(b"\r\n\r\n")
                    parte_cabecalhos = dados_resposta[:fim_cabecalho].decode('utf-8')
                    
                    #Verifica se tem Content-Length
                    tamanho_conteudo = 0
                    for linha in parte_cabecalhos.split('\r\n'):
                        if linha.lower().startswith('content-length:'):
                            tamanho_conteudo = int(linha.split(':')[1].strip())
                            break
                    
                    if tamanho_conteudo > 0:
                        inicio_corpo = fim_cabecalho + 4
                        corpo_recebido = len(dados_resposta) - inicio_corpo
                        if corpo_recebido >= tamanho_conteudo:
                            break
                    else:
                        break
            
            tempo_recepcao = time.time() - inicio_recepcao
            tempo_total = time.time() - tempo_inicio
            
            socket_cliente.close()
            
            #Parse da resposta
            texto_resposta = dados_resposta.decode('utf-8')
            
            #Dicionário de cabeçalhos
            cabecalhos = {}
            
            if "\r\n\r\n" in texto_resposta:
                parte_cabecalhos, parte_corpo = texto_resposta.split("\r\n\r\n", 1)
                linhas_cabecalhos = parte_cabecalhos.split('\r\n')
                linha_status = linhas_cabecalhos[0]
                codigo_status = int(linha_status.split(' ')[1])
                
                #Parse dos cabeçalhos
                for linha in linhas_cabecalhos[1:]:
                    if ': ' in linha:
                        chave, valor = linha.split(': ', 1)
                        cabecalhos[chave] = valor
            else:
                codigo_status = 0
                parte_corpo = ""
            
            return {
                'codigo_status': codigo_status,
                'corpo': parte_corpo,
                'cabecalhos': cabecalhos,
                'tempo_resposta': tempo_total,
                'tempo_conexao': tempo_conexao,
                'tempo_envio': tempo_envio,
                'tempo_recepcao': tempo_recepcao,
                'sucesso': True
            }
            
        except Exception as e:
            return {
                'codigo_status': 0,
                'corpo': "",
                'cabecalhos': {},
                'tempo_resposta': time.time() - tempo_inicio if 'tempo_inicio' in locals() else 0,
                'tempo_conexao': 0,
                'tempo_envio': 0,
                'tempo_recepcao': 0,
                'sucesso': False,
                'erro': str(e)
            }

if __name__ == "__main__":
    print("Este e o modulo cliente.py")
    print("Para executar testes, use: python3 testes/teste_completo.py")
    print("Para testes automatizados, use: python3 testes/teste_completo.py --completo")
