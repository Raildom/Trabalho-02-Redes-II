#Servidor Web Sequencial (Síncrono)
#Implementa um servidor que atende uma requisição por vez

import socket
import json
import time
from datetime import datetime
from configuracao import PORTA_SERVIDOR, ID_CUSTOMIZADO
import os

class ServidorWebSequencial:
    def __init__(self, host = '0.0.0.0', porta = PORTA_SERVIDOR):
        self.host = host
        self.porta = porta
        self.socket_servidor = None
        self.contador_requisicoes = 0
        
    def iniciar(self):
        #Inicia o servidor sequencial
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket_servidor.bind((self.host, self.porta))
            self.socket_servidor.listen(1)  #Fila de apenas 1 conexão
            print(f"Servidor Sequencial iniciado em {self.host}:{self.porta}")
            
            while True:
                socket_cliente, endereco_cliente = self.socket_servidor.accept()
                print(f"Conexão aceita de {endereco_cliente}")
                self.processar_requisicao(socket_cliente, endereco_cliente)
                
        except KeyboardInterrupt:
            print("\nServidor interrompido pelo usuário")
        except Exception as e:
            print(f"Erro no servidor: {e}")
        finally:
            self.parar()

    def processar_requisicao(self, socket_cliente, endereco_cliente):
        #Processa uma requisição HTTP
        try:
            tempo_inicio = time.time()
            #Recebe a requisição
            dados_requisicao = socket_cliente.recv(4096).decode('utf-8')
            if not dados_requisicao:
                return
            #Parse da requisição HTTP
            linhas_requisicao = dados_requisicao.split('\n')
            linha_requisicao = linhas_requisicao[0].strip()
            metodo, caminho, versao = linha_requisicao.split(' ')
            
            #Extrai headers
            cabecalhos = {}
            for linha in linhas_requisicao[1:]:
                if ':' in linha:
                    chave, valor = linha.split(':', 1)
                    cabecalhos[chave.strip()] = valor.strip()
            
            #Verifica o cabeçalho customizado
            id_customizado = cabecalhos.get('X-Custom-ID', '')
            
            #Validação obrigatória do X-Custom-ID
            if not id_customizado:
                resposta = self.gerar_resposta_erro(400, "Bad Request - X-Custom-ID obrigatório", id_customizado)
                socket_cliente.send(resposta.encode('utf-8'))
                return
            
            self.contador_requisicoes += 1
            
            #Gera resposta baseada no método e path
            resposta = self.gerar_resposta(metodo, caminho, id_customizado, tempo_inicio)
            
            #Envia resposta
            socket_cliente.send(resposta.encode('utf-8'))
            
            tempo_processamento = time.time() - tempo_inicio
            print(f"Requisição {self.contador_requisicoes} processada em {tempo_processamento:.4f}s")
            
        except Exception as e:
            print(f"Erro ao processar requisição: {e}")
            resposta_erro = self.gerar_resposta_erro(500, "Erro Interno do Servidor")
            socket_cliente.send(resposta_erro.encode('utf-8'))
        finally:
            socket_cliente.close()
    
    def gerar_resposta(self, metodo, caminho, id_customizado, tempo_inicio):
        #Gera resposta HTTP baseada no método e path

        #Simula diferentes tipos de processamento
        if caminho == '/lento':
            time.sleep(2)  #Simula processamento lento
        elif caminho == '/medio':
            time.sleep(0.5)  #Processamento médio
        #Path '/' ou '/rapido' - processamento rápido (sem delay)
        
        dados_resposta = {
            "tipo_servidor": "sequencial",
            "metodo": metodo,
            "caminho": caminho,
            "timestamp": datetime.now().isoformat(),
            "contador_requisicoes": self.contador_requisicoes,
            "id_customizado_recebido": id_customizado,
            "id_customizado_esperado": ID_CUSTOMIZADO,
            "id_customizado_valido": id_customizado == ID_CUSTOMIZADO,
            "tempo_processamento": time.time() - tempo_inicio,
            "mensagem": f"Resposta do servidor sequencial para {metodo} {caminho}"
        }
        
        if metodo == 'GET':
            if caminho == '/':
                dados_resposta["conteudo"] = "Página inicial do servidor sequencial"
            elif caminho == '/status':
                dados_resposta["conteudo"] = {
                    "status_servidor": "rodando",
                    "total_requisicoes": self.contador_requisicoes,
                    "tipo_servidor": "sequencial"
                }
            elif caminho in ['/rapido', '/medio', '/lento']:
                dados_resposta["conteudo"] = f"Endpoint {caminho} processado"
            else:
                return self.gerar_resposta_erro(404, "Não Encontrado", id_customizado)
                
        elif metodo == 'POST':
            if caminho == '/dados':
                dados_resposta["conteudo"] = "Dados recebidos via POST"
            else:
                return self.gerar_resposta_erro(404, "Não Encontrado", id_customizado)
                
        else:
            return self.gerar_resposta_erro(405, "Método Não Permitido", id_customizado)
        
        resposta_json = json.dumps(dados_resposta, indent=2)
        
        resposta = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Content-Length: {len(resposta_json)}\r
Server: ServidorSequencial/1.0\r
X-Server-Type: sequencial\r
X-Custom-ID: {id_customizado}\r
Connection: close\r
\r
{resposta_json}"""
        
        return resposta
    
    def gerar_resposta_erro(self, codigo_status, texto_status, id_customizado=""):
        #Gera resposta de erro HTTP
        dados_erro = {
            "erro": codigo_status,
            "mensagem": texto_status,
            "tipo_servidor": "sequencial",
            "timestamp": datetime.now().isoformat()
        }
        
        resposta_json = json.dumps(dados_erro, indent=2)
        
        resposta = f"""HTTP/1.1 {codigo_status} {texto_status}\r
Content-Type: application/json\r
Content-Length: {len(resposta_json)}\r
Server: ServidorSequencial/1.0\r
X-Custom-ID: {id_customizado}\r
Connection: close\r
\r
{resposta_json}"""
        
        return resposta
    
    def parar(self):
        #Para o servidor
        if self.socket_servidor:
            self.socket_servidor.close()
            print("Servidor sequencial parado")

if __name__ == "__main__":
    servidor = ServidorWebSequencial()
    servidor.iniciar()
