# Trabalho de Redes II - Servidores HTTP

## Aluno: 
   Raildom da Rocha Sobrinho
## Matrícula: 
   20239057601

## Link do GITHUB

**Repositório**: [https://github.com/Raildom/Trabalho-01-Redes-II.git]

## Link do Youtube

**Vídeo de Demonstração**: [https://youtu.be/4h5CTQPBs_Y]

---

### tecnologias Utilizadas
- Python 3.9 ou superior
- Docker e Docker Compose
- Bibliotecas Python: socket, threading, time, matplotlib, numpy, argparse

---

## Como Executar o Projeto

### Pré-requisitos
- Docker e Docker Compose instalados

### Passos para Execução

1. **Clone o repositório**:
```bash
git clone <https://github.com/Raildom/Trabalho-01-Redes-II.git>
cd Trabalho-01-Redes-II
```

2. **Execute o menu principal**:
```bash
python3 run_project.py
```

3. **Opções disponíveis no menu**:
   - `1` - Iniciar servidores Docker
   - `2` - Teste de conectividade
   - `3` - Executar testes de carga
   - `4` - Analisar resultados e gerar gráficos
   - `5` - Entrar no container de teste
   - `6` - Executar tudo automaticamente
   - `0` - Sair

4. **Execução completa automática via menu** (recomendado):
```bash
echo "6" | python3 run_project.py
```

### Execução Manual via Terminal

#### Opção 1 - Iniciar Servidores Docker
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

Verificar se os containers estão rodando:
```bash
docker ps
```

#### Opção 2 - Teste de Conectividade
Execute diretamente:
```bash
docker exec -it cliente_teste python3 -c "
from testes.teste_completo import TestadorProjeto
testador = TestadorProjeto()
testador.teste_conectividade_basica('docker')"
```

#### Opção 3 - Executar Testes de Carga
Execute testes completos:
```bash
docker exec -it cliente_teste python3 /app/testes/teste_completo.py --completo
```

Ou teste endpoints específicos:
```bash
docker exec -it cliente_teste python3 -c "
from testes.teste_completo import TestadorProjeto
testador = TestadorProjeto()
testador.teste_endpoints('docker')
"
```

#### Opção 4 - Analisar Resultados e Gerar Gráficos
```bash
docker exec -it cliente_teste python3 /app/testes/analisar_resultados.py
```

Os gráficos serão salvos em `resultados/graficos/`.

Para visualizar os gráficos no host:
```bash
ls -lh resultados/graficos/
```

#### Opção 5 - Entrar no Container de Teste
```bash
docker exec -it cliente_teste bash
```

Dentro do container, você pode executar comandos manualmente:
```bash
#Testar servidor sequencial
PYTHONPATH=/app/src python3 -c "from src.cliente import ClienteHTTP; c = ClienteHTTP('76.1.0.10'); print(c.enviar_requisicao('GET', '/'))"

#Testar servidor concorrente
PYTHONPATH=/app/src python3 -c "from src.cliente import ClienteHTTP; c = ClienteHTTP('76.1.0.11'); print(c.enviar_requisicao('GET', '/'))"

#Ver resultados salvos
ls -lh /app/resultados/

#Sair do container
exit
```

#### Opção 6 - Executar Tudo Automaticamente
```bash
#Iniciar servidores
docker-compose -f docker/docker-compose.yml up --build -d

#Aguardar servidores iniciarem
sleep 2

#Executar testes completos
docker exec -it cliente_teste python3 /app/testes/teste_completo.py --completo

#Gerar análises e gráficos
docker exec -it cliente_teste python3 /app/testes/analisar_resultados.py
```

#### Parar e Limpar Containers
```bash
#Parar containers
docker-compose -f docker/docker-compose.yml down

#Remover volumes (limpar dados)
docker-compose -f docker/docker-compose.yml down -v

#Visualizar logs dos servidores
docker-compose -f docker/docker-compose.yml logs -f sequencial
docker-compose -f docker/docker-compose.yml logs -f concorrente
```

---

## Estrutura do Projeto (Hierarquia de Diretórios)

```
Trabalho-01-Redes-II/
│
├── README.md                          #Documentação do projeto
├── requisitos.txt                     #Dependências Python
├── run_project.py                     #Menu principal de execução
├── Avaliacao Redes 2 2025-2 .pdf      #Especificação do trabalho
│
├── src/                               #Código-fonte principal
│   ├── servidor_sequencial.py         #Implementação do servidor sequencial
│   ├── servidor_concorrente.py        #Implementação do servidor concorrente
│   ├── cliente.py                     #Cliente HTTP para testes
│   └── configuracao.py                #Configurações compartilhadas (porta, IDs, etc)
│
├── docker/                            #Arquivos Docker
│   ├── docker-compose.yml             #Orquestração dos containers
│   ├── Dockerfile.sequencial          #Imagem do servidor sequencial
│   ├── Dockerfile.concorrente         #Imagem do servidor concorrente
│   └── Dockerfile.cliente             #Imagem do cliente de testes
│
├── testes/                            #Scripts de teste e análise
│   ├── teste_completo.py              #Suite completa de testes
│   └── analisar_resultados.py         #Geração de gráficos e análises
│
├── resultados/                        #Resultados gerados (criado automaticamente)
│   └── graficos/                      #Gráficos PNG gerados pelos testes
```

### Descrição dos Componentes

#### **src/** - Código-fonte
- `servidor_sequencial.py`: Servidor que processa requisições uma de cada vez
- `servidor_concorrente.py`: Servidor que usa threads para processar múltiplas requisições simultaneamente
- `cliente.py`: Cliente HTTP customizado usando sockets TCP
- `configuracao.py`: Constantes compartilhadas (PORTA_SERVIDOR, ID_CUSTOMIZADO, MAX_CONEXOES)

#### **docker/** - Containerização
- `docker-compose.yml`: Orquestra 3 containers na rede 76.1.0.0/16
- `Dockerfile.sequencial`: Container do servidor sequencial (76.1.0.10:8080)
- `Dockerfile.concorrente`: Container do servidor concorrente (76.1.0.11:8080)
- `Dockerfile.cliente`: Container cliente de testes (76.1.0.20)

#### **testes/** - Testes e Análises
- `teste_completo.py`: Executa testes de conectividade, endpoints e carga
- `analisar_resultados.py`: Processa dados e gera gráficos comparativos

#### **resultados/** - Dados Gerados
- `graficos/`: Gráficos PNG comparativos (throughput, tempo de resposta, taxa de sucesso)

---