#Servidor Web Concorrente (Assíncrono)
#Implementa um servidor que atende múltiplas requisições simultaneamente usando threads

import socket
import json
import time
import threading
from datetime import datetime
from configuracao import PORTA_SERVIDOR, ID_CUSTOMIZADO, MAX_CONEXOES

class ServidorWebConcorrente:
    def __init__(self, host = '0.0.0.0', porta = PORTA_SERVIDOR):
        self.host = host
        self.porta = porta
        self.socket_servidor = None
        self.contador_requisicoes = 0
        self.lock = threading.Lock()
        self.conexoes_ativas = 0
        
    def iniciar(self):
        #Inicia o servidor concorrente"
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket_servidor.bind((self.host, self.porta))
            self.socket_servidor.listen(MAX_CONEXOES)
            print(f"Servidor Concorrente iniciado em {self.host}:{self.porta}")
            print(f"Máximo de {MAX_CONEXOES} conexões simultâneas")
            
            while True:
                socket_cliente, endereco_cliente = self.socket_servidor.accept()
                
                #Cria uma thread para cada cliente
                thread_cliente = threading.Thread(
                    target=self.gerenciar_cliente,
                    args=(socket_cliente, endereco_cliente)
                )
                thread_cliente.daemon = True
                thread_cliente.start()
                
        except KeyboardInterrupt:
            print("\nServidor interrompido pelo usuário")
        except Exception as e:
            print(f"Erro no servidor: {e}")
        finally:
            self.parar()
    
    def gerenciar_cliente(self, socket_cliente, endereco_cliente):
        #Gerencia a conexão com um cliente em uma thread separada
        with self.lock:
            self.conexoes_ativas += 1
            id_conexao = self.conexoes_ativas
            
        print(f"Conexão {id_conexao} aceita de {endereco_cliente}")
        
        try:
            self.processar_requisicao(socket_cliente, endereco_cliente, id_conexao)
        finally:
            with self.lock:
                self.conexoes_ativas -= 1
            print(f"Conexão {id_conexao} finalizada")
    
    def processar_requisicao(self, socket_cliente, endereco_cliente, id_conexao):
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
                resposta_erro = self.gerar_resposta_erro(400, "Bad Request - X-Custom-ID obrigatório", id_conexao, id_customizado)
                socket_cliente.send(resposta_erro.encode('utf-8'))
                return
            
            with self.lock:
                self.contador_requisicoes += 1
                requisicao_atual = self.contador_requisicoes
            
            #Gera resposta baseada no método e path
            resposta = self.gerar_resposta(metodo, caminho, id_customizado, tempo_inicio, requisicao_atual, id_conexao)
            
            #Envia resposta
            socket_cliente.send(resposta.encode('utf-8'))
            
            tempo_processamento = time.time() - tempo_inicio
            print(f"Requisição {requisicao_atual} (conexão {id_conexao}) processada em {tempo_processamento:.4f}s")
            
        except Exception as e:
            print(f"Erro ao processar requisição na conexão {id_conexao}: {e}")
            id_customizado = ""  #Em caso de erro, pode não ter sido extraído
            resposta_erro = self.gerar_resposta_erro(500, "Erro Interno do Servidor", id_conexao, id_customizado)
            socket_cliente.send(resposta_erro.encode('utf-8'))
        finally:
            socket_cliente.close()
    
    def gerar_resposta(self, metodo, caminho, id_customizado, tempo_inicio, num_requisicao, id_conexao):
        #Gera resposta HTTP baseada no método e path
        
        #Simula diferentes tipos de processamento
        if caminho == '/lento':
            time.sleep(2)  #Simula processamento lento
        elif caminho == '/medio':
            time.sleep(0.5)  #Processamento médio
        #Path '/' ou '/rapido' - processamento rápido (sem delay)
        
        with self.lock:
            ativas_atuais = self.conexoes_ativas
        
        dados_resposta = {
            "tipo_servidor": "concorrente",
            "metodo": metodo,
            "caminho": caminho,
            "timestamp": datetime.now().isoformat(),
            "contador_requisicoes": num_requisicao,
            "id_conexao": id_conexao,
            "conexoes_ativas": ativas_atuais,
            "id_customizado_recebido": id_customizado,
            "id_customizado_esperado": ID_CUSTOMIZADO,
            "id_customizado_valido": id_customizado == ID_CUSTOMIZADO,
            "tempo_processamento": time.time() - tempo_inicio,
            "id_thread": threading.current_thread().ident,
            "mensagem": f"Resposta do servidor concorrente para {metodo} {caminho}"
        }
        
        if metodo == 'GET':
            if caminho == '/':
                dados_resposta["conteudo"] = "Página inicial do servidor concorrente"
            elif caminho == '/status':
                dados_resposta["conteudo"] = {
                    "status_servidor": "rodando",
                    "total_requisicoes": num_requisicao,
                    "conexoes_ativas": ativas_atuais,
                    "tipo_servidor": "concorrente"
                }
            elif caminho in ['/rapido', '/medio', '/lento']:
                dados_resposta["conteudo"] = f"Endpoint {caminho} processado"
            else:
                return self.gerar_resposta_erro(404, "Não Encontrado", id_conexao, id_customizado)
                
        elif metodo == 'POST':
            if caminho == '/dados':
                dados_resposta["conteudo"] = "Dados recebidos via POST"
            else:
                return self.gerar_resposta_erro(404, "Não Encontrado", id_conexao, id_customizado)
                
        else:
            return self.gerar_resposta_erro(405, "Método Não Permitido", id_conexao, id_customizado)
        
        resposta_json = json.dumps(dados_resposta, indent=2)
        
        resposta = f"""HTTP/1.1 200 OK\r
Content-Type: application/json\r
Content-Length: {len(resposta_json)}\r
Server: ServidorConcorrente/1.0\r
X-Server-Type: concorrente\r
X-Connection-ID: {id_conexao}\r
X-Thread-ID: {threading.current_thread().ident}\r
X-Custom-ID: {id_customizado}\r
Connection: close\r
\r
{resposta_json}"""
        
        return resposta
    
    def gerar_resposta_erro(self, codigo_status, texto_status, id_conexao, id_customizado=""):
        #Gera resposta de erro HTTP
        dados_erro = {
            "erro": codigo_status,
            "mensagem": texto_status,
            "tipo_servidor": "concorrente",
            "id_conexao": id_conexao,
            "id_thread": threading.current_thread().ident,
            "timestamp": datetime.now().isoformat()
        }
        
        resposta_json = json.dumps(dados_erro, indent=2)
        
        resposta = f"""HTTP/1.1 {codigo_status} {texto_status}\r
Content-Type: application/json\r
Content-Length: {len(resposta_json)}\r
Server: ServidorConcorrente/1.0\r
X-Connection-ID: {id_conexao}\r
X-Custom-ID: {id_customizado}\r
Connection: close\r
\r
{resposta_json}"""
        
        return resposta
    
    def parar(self):
        #Para o servidor
        if self.socket_servidor:
            self.socket_servidor.close()
            print("Servidor concorrente parado")

if __name__ == "__main__":
    servidor = ServidorWebConcorrente()
    servidor.iniciar()
