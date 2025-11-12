# Trabalho de Redes II - Comparação de Servidores Web

## Aluno: 
   Raildom da Rocha Sobrinho
## Matrícula: 
   20239057601

## Link do GITHUB

**Repositório**: [https://github.com/Raildom/Trabalho-02-Redes-II.git]

## Link do Youtube

**Vídeo de Demonstração**: [EM BREVE]

---

## Objetivo

Configurar e comparar o desempenho de dois servidores web de mercado distintos (**Nginx** e **Apache**) utilizando uma pilha de observabilidade (**Prometheus + Grafana**), a fim de ressaltar pontos de vantagem e desvantagem de cada abordagem em diferentes cenários de carga.

---

## Tecnologias Utilizadas

### Servidores Web
- **Nginx** (Alpine) - Servidor assíncrono orientado a eventos
- **Apache HTTP Server 2.4** (Alpine) - Servidor com MPM Event

### Observabilidade
- **Prometheus** - Coleta e armazenamento de métricas
- **Grafana** - Visualização e dashboards
- **nginx-prometheus-exporter** - Exportador de métricas do Nginx
- **apache_exporter** - Exportador de métricas do Apache

### Infraestrutura
- **Docker** e **Docker Compose** - Containerização
- **Python 3** - Scripts de testes e automação

### Protocolo
- **HTTP** - Comunicação cliente-servidor
- **TCP/IP** - Camadas de rede

---

## Arquitetura do Projeto

### Configuração de Rede
- **Sub-rede**: 76.1.0.0/16 (baseada nos últimos 4 dígitos da matrícula: 7601)
- **Nginx**: 76.1.0.10:8080 (porta 80 interna)
- **Apache**: 76.1.0.11:8081 (porta 80 interna)
- **Prometheus**: 76.1.0.30:9090
- **Grafana**: 76.1.0.40:3000
- **Cliente de Testes**: 76.1.0.20

### Cabeçalho HTTP Personalizado
Todas as requisições incluem o cabeçalho:
```
X-Custom-ID: 57ce9496f1bb17f33d6558b5f6e77f04c471893796c40f96bbf540d62054d2d7
```
Hash SHA-256 calculado a partir de: "20239057601 Raildom"

---

## Como Executar o Projeto

### Pré-requisitos
- Docker e Docker Compose instalados
- Python 3.7+ (para scripts de geração de arquivos)

### Passos para Execução

1. **Clone o repositório**:
```bash
git clone https://github.com/Raildom/Trabalho-02-Redes-II.git
cd Trabalho-02-Redes-II
```

2. **Gere os arquivos estáticos de teste**:
```bash
python3 src/gerar_arquivos_estaticos.py
```

3. **Inicie os contêineres**:
```bash
docker-compose -f docker/docker-compose.yml up --build -d
```

4. **Aguarde os serviços iniciarem** (cerca de 30 segundos)

5. **Verifique se os contêineres estão rodando**:
```bash
docker ps
```

Você deve ver 5 contêineres:
- servidor_nginx
- servidor_apache  
- prometheus
- grafana
- cliente_teste

6. **Execute os testes de carga**:
```bash
docker exec -it cliente_teste python3 /app/testes/teste_carga.py
```

7. **Acesse as ferramentas de monitoramento**:

**Prometheus** (métricas):
```
http://localhost:9090
```

**Grafana** (visualização):
```
http://localhost:3000
Usuário: admin
Senha: admin
```

8. **Para parar os contêineres**:
```bash
docker-compose -f docker/docker-compose.yml down
```

---

## Endpoints Disponíveis

### Nginx (http://localhost:8080)

| Endpoint | Método | Descrição | Tamanho |
|----------|--------|-----------|---------|
| `/` | GET | Página inicial | ~2 KB |
| `/saude` | GET | Verificação de saúde | ~5 bytes |
| `/api/pequeno` | GET | JSON pequeno | ~60 bytes |
| `/api/medio` | GET | JSON médio | ~400 bytes |
| `/api/grande` | GET | JSON grande | ~1 KB |
| `/estatico/` | GET | Listagem de arquivos | Variável |
| `/estatico/pequeno-1kb.txt` | GET | Arquivo 1KB | 1 KB |
| `/estatico/enorme-10mb.txt` | GET | Arquivo 10MB | 10 MB |
| `/status_nginx` | GET | Status (interno) | Restrito |

### Apache (http://localhost:8081)

| Endpoint | Método | Descrição | Tamanho |
|----------|--------|-----------|---------|
| `/` | GET | Página inicial | ~2 KB |
| `/saude` | GET | Verificação de saúde | Variável |
| `/api/pequeno` | GET | JSON pequeno | ~60 bytes |
| `/api/medio` | GET | JSON médio | ~250 bytes |
| `/api/grande` | GET | JSON grande | ~550 bytes |
| `/estatico/` | GET | Listagem de arquivos | Variável |
| `/estatico/medio-100kb.txt` | GET | Arquivo 100KB | 100 KB |
| `/estatico/grande-5mb.txt` | GET | Arquivo 5MB | 5 MB |
| `/status-servidor` | GET | Status (interno) | Restrito |

---

## Métricas Coletadas

### Prometheus - Consultas Úteis

```promql
# Taxa de requisições por segundo
rate(nginx_http_requests_total[1m])
rate(apache_accesses_total[1m])

# Conexões/Workers ativos
nginx_connections_active
apache_workers_busy

# Throughput (bytes transferidos)
rate(nginx_http_response_bytes_total[1m])
rate(apache_sent_kilobytes_total[1m]) * 1024

# Tempo de atividade
apache_uptime_seconds_total
```

### Métricas Avaliadas nos Testes

1. **Requisições por Segundo (RPS)**
   - Fórmula: RPS = Total de Requisições / Tempo Total (segundos)

2. **Latência**
   - P50 (Mediana): 50% das requisições abaixo deste tempo
   - P95: 95% das requisições abaixo deste tempo  
   - P99: 99% das requisições abaixo deste tempo

3. **Taxa de Sucesso**
   - Percentual de requisições completadas com sucesso

4. **Desvio Padrão**
   - Variabilidade dos tempos de resposta

---

## Cenários de Teste

### Teste 1: Endpoints de API
- **Objetivo**: Avaliar latência de respostas JSON
- Endpoints: /api/pequeno, /api/medio, /api/grande
- 1000 requisições por endpoint
- 50 requisições concorrentes

### Teste 2: Arquivos Estáticos
- **Objetivo**: Comparar transferência de arquivos
- Tamanhos: 1KB, 100KB, 1MB
- 500 requisições por arquivo
- 30 requisições concorrentes

### Teste 3: Pico de Carga (Spike)
- **Objetivo**: Avaliar comportamento sob carga repentina
- 5000 requisições
- 200 requisições concorrentes

### Teste 4: Carga Sustentada
- **Objetivo**: Testar estabilidade sob carga contínua
- 10000 requisições
- 100 requisições concorrentes

---

## Estrutura do Projeto

```
Trabalho-02-Redes-II/
│
├── README.md                                  # Documentação
├── requisitos.txt                             # Dependências Python
├── run_project.py                             # Menu principal (legado)
│
├── src/                                       # Código-fonte
│   ├── cliente.py                             # Cliente HTTP
│   ├── configuracao.py                        # Configurações (IDs, rede)
│   └── gerar_arquivos_estaticos.py            # Gerador de arquivos
│
├── docker/                                    # Arquivos Docker
│   ├── docker-compose.yml                     # Orquestração
│   ├── Dockerfile.nginx                       # Imagem Nginx
│   ├── Dockerfile.apache                      # Imagem Apache
│   ├── Dockerfile.cliente                     # Imagem Cliente
│   ├── nginx.conf                             # Configuração Nginx
│   ├── httpd.conf                             # Configuração Apache
│   ├── pagina_inicial_nginx.html              # Página inicial Nginx
│   ├── pagina_inicial_apache.html             # Página inicial Apache
│   ├── prometheus.yml                         # Configuração Prometheus
│   └── grafana-fontes-dados.yml               # Datasource Grafana
│
├── testes/                                    # Scripts de teste
│   ├── teste_carga.py                         # Testes de carga principais
│   └── analisar_resultados.py                 # Análise estatística
│
├── conteudo-estatico/                         # Arquivos de teste
│   ├── pequeno-1kb.txt                        # 1 KB
│   ├── pequeno-10kb.txt                       # 10 KB
│   ├── medio-100kb.txt                        # 100 KB
│   ├── medio-500kb.txt                        # 500 KB
│   ├── grande-1mb.txt                         # 1 MB
│   ├── grande-5mb.txt                         # 5 MB
│   └── enorme-10mb.txt                        # 10 MB
│
└── resultados/                                # Resultados dos testes
    └── (gerado automaticamente)
```

---

## Justificativa das Escolhas

### Por que Nginx?
- **Arquitetura assíncrona**: Melhor para alta concorrência
- **Baixo uso de memória**: Eficiente para servir arquivos estáticos
- **Performance**: Reconhecido por velocidade

### Por que Apache?
- **Maturidade**: Servidor estabelecido com ampla documentação
- **Flexibilidade**: Suporta .htaccess e módulos dinâmicos
- **Comparação justa**: Referência tradicional para benchmarks

### Por que Prometheus + Grafana?
- **Código aberto**: Gratuito e amplamente adotado
- **Integração Docker**: Fácil deployment em contêineres
- **Flexibilidade**: Queries poderosas com PromQL
- **Visualização**: Dashboards profissionais

---

## Referências

- [Documentação Nginx](https://nginx.org/en/docs/)
- [Documentação Apache](https://httpd.apache.org/docs/)
- [Documentação Prometheus](https://prometheus.io/docs/)
- [Documentação Grafana](https://grafana.com/docs/)
- [Documentação Docker](https://docs.docker.com/)
- [Protocolo HTTP RFC 2616](https://tools.ietf.org/html/rfc2616)

---

**Aluno:** Raildom da Rocha Sobrinho  
**Matrícula:** 20239057601  
**Data:** 12/11/2025
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