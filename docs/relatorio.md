## Ex3

### Avaliação sob a Tríade CIA
* Confidencialidade (Alto Peso - LGPD): Garantida pelo isolamento de dados na camada de apresentação. O uso do ConsultaResponse com extra="ignore" assegura que campos internos (como token_auditoria e notas_medicas) fiquem restritos ao banco de dados e nunca vazem nos payloads JSON consumidos pelos clientes externos.

* Integridade: Protegida na entrada de dados via Pydantic (extra="forbid" no ConsultaBase), que impede a injeção de atributos não documentados (Mass Assignment) por usuários mal-intencionados. Na camada de visualização (HTML), a integridade da sessão do usuário é mantida pelo auto-escaping do Jinja2, que neutraliza scripts maliciosos (Stored XSS) salvos no banco.

* Disponibilidade: Suportada pela arquitetura modular (separações lógicas em routers, models e database), que previne gargalos de manutenção e facilita o isolamento de falhas. O uso do FastAPI (assíncrono por natureza) e a implementação de testes automatizados (pytest) previnem regressões que poderiam causar indisponibilidade em novas entregas.

|Framework de Referência  |Controle Implementado na API                                               |Ameaça/Vulnerabilidade Mitigada                                                                   |
|-------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
|OWASP API Security Top 10|Filtro de saída estrito via response_model no roteador FastAPI.            |API3:2023 (Broken Object Property Level Authorization): Previne vazamento de dados (Data Leakage).|
|OWASP API Security Top 10|model_config = ConfigDict(extra="forbid") na validação de entrada Pydantic.|API3:2023 (Broken Object Property Level Authorization): Bloqueia Mass Assignment.                 |
|MITRE CWE / CAPEC        |Motor de template Jinja2 renderizando variáveis sem o filtro &#124; safe.       |CWE-79 / CAPEC-86: Neutraliza injeção de Cross-Site Scripting (Stored XSS) no painel web.         |
|NIST SSDF (V 1.1)        |Isolamento de ambiente (venv) e testes automatizados (pytest).             |PO.1.3 / PW.2: Proteção do ambiente de desenvolvimento e verificação contínua de software.        |

---
### DFD

    Vide imagem Ex_DFD.png
---

## Ex4

### Misuse Cases

1. Misuse Case 1: Enumeração de IDs por Parceiro B2B (BOLA/IDOR)

    * Ator: Laboratório parceiro comprometido ou mal-intencionado.

    * Ação: O atacante utiliza credenciais legítimas de acesso, mas manipula sequencialmente o parâmetro consulta_id na rota GET /consultas/{id}.

    * Objetivo: Acessar, raspar e exfiltrar dados sensíveis de consultas de pacientes (nomes, horários, médicos) aos quais o laboratório não deveria ter acesso.

2. Misuse Case 2: Elevação de Privilégio Interna (Mass Assignment)

    * Ator: Funcionário interno (ex: Recepcionista).

    * Ação: Ao enviar um PUT /consultas/{id} para atualizar o horário de uma consulta, o recepcionista injeta campos não documentados no JSON, como {"status": "cancelada", "token_auditoria": "falsificado"}.

    * Objetivo: Alterar estados internos do sistema e mascarar trilhas de auditoria, assumindo controle de fluxos exclusivos de administradores ou médicos.

3. Misuse Case 3: Envenenamento do Painel da Recepção (Stored XSS)

    * Ator: Paciente ou atacante externo via API pública.

    * Ação: O atacante envia uma string contendo um payload JavaScript malicioso (\<script>...) no campo de nome do paciente ao tentar agendar uma consulta.

    * Objetivo: Fazer com que o script seja armazenado no banco e executado no navegador da recepcionista quando ela abrir a tela HTML da agenda diária, roubando seu token de sessão.

### STRIDE

#### Componente A: Endpoints REST (Roteadores FastAPI)
* S (Spoofing - Falsificação de Identidade): Um atacante ou funcionário pode forjar requisições fingindo ser um médico ou administrador para acessar dados restritos.

    * Mitigação Planejada: Implementação de Autenticação JWT com assinaturas criptográficas robustas (HS256/RS256) para garantir a identidade real do chamador.

* R (Repudiation - Repúdio): Um usuário legítimo (ex: recepcionista) cancela ou altera a consulta de um paciente e posteriormente nega a autoria da ação, impossibilitando a responsabilização por falta de provas.

    * Mitigação Planejada: Implementação de trilhas de auditoria irrefutáveis. O sistema extrairá a identidade exata do usuário autenticado no JWT e a salvará obrigatoriamente no campo token_auditoria do banco de dados em qualquer operação de escrita (POST/PUT/DELETE).

* I (Information Disclosure - Divulgação de Informação): Acesso não autorizado a prontuários de outros pacientes via manipulação do ID na URL (BOLA/IDOR).

    * Mitigação Planejada: Middleware de verificação de posse (Ownership) associado à identidade validada do token JWT.

* D (Denial of Service - Negação de Serviço): O envio automatizado e massivo de requisições de criação de consultas pode esgotar os recursos da API ou do banco de dados, paralisando o atendimento da clínica.

    * Mitigação Planejada: Implementação de limite de taxa (Rate Limiting) no API Gateway ou via middleware.

* E (Elevation of Privilege - Elevação de Privilégio): Uma recepcionista manipulando endpoints que deveriam ser exclusivos de administradores ou médicos.

    * Mitigação Planejada: Controle de Acesso Baseado em Papéis (RBAC) validando a role extraída do JWT antes de liberar a execução da rota.

#### Componente B: Camada de Validação (Modelos Pydantic)
* T (Tampering - Violação de Dados): Modificação de atributos internos protegidos enviando payloads JSON customizados (Elevação de Privilégio via Mass Assignment).

    * Mitigação Atual: Configuração extra="forbid" nos modelos de entrada, barrando qualquer campo não documentado.

* I (Information Disclosure - Divulgação de Informação): A serialização padrão do banco para JSON vazar campos internos sigilosos como notas_medicas ou chaves de auditoria.

    * Mitigação Atual: Uso de response_model estritos com extra="ignore" (Data Leakage Prevention).

#### Componente C: Interface Web (Páginas HTML com Jinja2)
* T (Tampering - Violação de Dados): Injeção de código JavaScript malicioso no banco de dados que é executado no navegador da recepção (Stored XSS), visando o roubo de sessões.

    * Mitigação Atual: Uso de Auto-escaping ativo por padrão no framework Jinja2, convertendo imediatamente os caracteres de execução (como < e >) em entidades HTML inofensivas.

## Ex5

---
    Vide imagem Ex5.png
---

## Ex7

Dados de acesso M2M:

    * grant_type: client_credentials
    * client_id: lab_parceiro
    * client_secret: senha_super_secreta_b2b

## Ex8

### **Broken Object Level Authorization (BOLA / IDOR)**
* Localização no Código: Rota de leitura individual de consultas (GET /consultas/{consulta_id}).

* Padrão Vulnerável: O endpoint recebia um identificador único na URL (consulta_id), consultava o banco de dados e simplesmente retornava o documento JSON se ele existisse, sem checar a identidade ou o papel do usuário autenticado que fez a requisição.

* Impacto no Negócio: Qualquer usuário autenticado (ou um paciente com token válido) podia iterar sobre os IDs das consultas e ler prontuários, nomes e históricos médicos de terceiros.

```
@router.get("/{consulta_id}")
async def obter_consulta(consulta_id: PydanticObjectId):
    consulta = await Consulta.get(consulta_id)
    return consulta  # Falha: Não valida se o usuário logado é o dono ou admin!
```

### **Broken Object Property Level Authorization (Mass Assignment / Anti-Spoofing Failure)**
* Localização no Código: Modelo de entrada e rota de criação de consultas (POST /consultas/).

* Padrão Vulnerável: O esquema de requisição aceitava o campo profissional_nome diretamente no corpo do JSON da requisição HTTP (body), sem restringir quem podia definir essa propriedade.

* Impacto no Negócio: Um usuário comum ou um atacante podia enviar uma requisição forjando o nome de outro médico no payload, alterando a autoria e a responsabilidade clínica do registro (Quebra de Anti-Spoofing / Anti-Repúdio).

```
class ConsultaCreate(BaseModel):
    paciente_nome: str
    profissional_nome: str  # Falha: Permite injetar/forjar a identidade no payload
    data_hora: datetime
```

### **Server-Side Request Forgery (SSRF) / Security Misconfiguration (Acesso por Bypassing de Autenticação / Endpoints Expostos)**
* Localização no Código: Rotas administrativas de manutenção (DELETE /consultas/limpar) ou rotas expostas sem dependência de segurança.

* Padrão Vulnerável: Ausência de checagem de papéis (RBAC) ou de escopos OAuth2 na assinatura da função do endpoint. O endpoint confiava apenas que a rota existia ou estava escondida.

* Impacto no Negócio: Um usuário com papel de menor privilégio (ex: recepcionista ou laboratório) conseguia invocar ações administrativas destrutivas, como apagar todo o histórico de consultas do banco de dados.

```
@router.delete("/limpar")
async def limpar_todas_consultas():
    await Consulta.delete_all()  # Falha: Falta a dependência de RBAC (require_admin)
```

## Ex12

### **Estratégia DevSecOps: Posicionamento no SDLC e Security Gate**

| Ferramenta / Abordagem        | Fase do SDLC               | Justificativa de Negócio e Técnica                                                                                                                                               |
|-------------------------------|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| SAST (Análise Estática)       | Build / Pull Request (CI)  | Roda diretamente no código-fonte em segundos. Identifica senhas hardcoded, injeções e falhas lógicas antes do código ser mesclado (merge) na branch principal.                   |
| SCA (Composição/Dependências) | Build / Pull Request (CI)  | Avalia bibliotecas (requirements.txt). Bloqueia o build se uma dependência (ex: FastAPI, Beanie) tiver uma CVE (vulnerabilidade conhecida) recém-descoberta.                     |
| DAST (Análise Dinâmica)       | Homologação / Staging (CD) | Foca no comportamento da aplicação em execução. Testa a API compilada contra o OWASP Top 10 enviando payloads reais. Fica em Staging porque testes dinâmicos são mais demorados. |
| IAST (Análise Interativa)     | QA / Testes Funcionais     | Instrumenta a aplicação por dentro durante os testes automatizados do QA. Ideal para capturar fluxos de dados sensíveis da clínica em tempo real.                                |

### **Critério do Security Gate (Bloqueio do Pipeline)**

O pipeline de CI/CD será bloqueado sempre que o SAST ou o SCA encontrarem vulnerabilidades de severidade ALTA (High) ou CRÍTICA (Critical). Vulnerabilidades de nível Médio ou Baixo gerarão apenas alertas (warnings) e irão para o backlog técnico. Em sistemas de saúde, travar o pipeline por falsos-positivos de baixo impacto atrasa entregas críticas, mas falhas graves (como BOLA ou SQLi) violam as exigências legais de proteção de dados.

### **Priorização de Vulnerabilidades e Impacto (Threat Model)**

| Vulnerabilidade Mapeada                         | Score CVSS Estimado | Severidade | Impacto no Negócio (Justificativa)                                                                                                                   |
|-------------------------------------------------|---------------------|------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| BOLA (IDOR) - Leitura de prontuário de terceiro | 8.5                 | Alta       | Impacto: Violação severa de privacidade médica (LGPD/HIPAA). Quebra de confiança com o paciente e exposição da clínica a processos judiciais.        |
| BFLA - Limpeza total de consultas por não-admin | 8.1                 | Alta       | Impacto: Perda de disponibilidade e integridade. A exclusão da base de dados paralisa a operação da clínica e o atendimento aos pacientes.           |
| Mass Assignment - Falsificação do médico autor  | 7.5                 | Alta       | Impacto: Repúdio e fraude. Um prontuário com médico forjado invalida o histórico clínico e impossibilita a responsabilização legal por diagnósticos. |

## Ex13
### **OWASP Zap**
Vide HTML gerado pela ferramenta `2026-09-29-ZAP-Report-`

### **Consolidação Arquitetural e Testes de Segurança**

A aplicação FastAPI foi consolidada integrando autenticação híbrida (OAuth2 com JWT e MFA), validação estrita de entrada via Pydantic V2 (extra='forbid', Regex), persistência assíncrona segura e um SecurityHeadersMiddleware. A bateria de testes automatizados com pytest e mocking valida eficazmente as fronteiras de autorização (BOLA e BFLA) e a rejeição de pedidos maliciosos (XSS e Mass Assignment). A especificação OpenAPI expõe corretamente os esquemas de segurança e requisitos de validação sem vazar lógica de negócio.

### **Matriz de Correlação de Vulnerabilidades (Threat Model & OWASP ZAP)**

| **Ferramenta / Origem** | **Risco Identificado**                                                          | **Categoria OWASP**                                               | **Estado e Mitigação no Código**                                                                                                                                                                                                                                                                                                                                               |
|-------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **OWASP ZAP**           | Credenciais de Autenticação Capturadas (Risco Alto) na rota /token.             | A02:2021 - Cryptographic Failures / A07 - Authentication Failures | Mitigado (Requisito de Infraestrutura): O ZAP alerta para o tráfego em HTTP (texto claro) no localhost:8080 utilizando um mecanismo que revela o nome de utilizador e a senha. A autenticação por JWT gerada no projeto é segura; a criptografia em trânsito será garantida pelo certificado TLS/SSL no ambiente de produção, não transmitindo a senha de forma não encriptada |
| **OWASP ZAP**           | Content Security Policy (CSP) Not Set (Risco Médio) na rota do Swagger (/docs)  | A05:2021 - Security Misconfiguration                              | Corrigido: Mitigável através da expansão do SecurityHeadersMiddleware para incluir o cabeçalho CSP, o que mitiga ataques de injeção de dados e Cross Site Scripting (XSS) no frontend da documentação                                                                                                                                                                          |
| **OWASP ZAP**           | Sub Resource Integrity Missing (Risco Médio) no carregamento do swagger-ui.css. | A05:2021 - Security Misconfiguration                              | Risco Aceito (Baixo Impacto): Refere-se à ausência do atributo de integridade em recursos externos injetados automaticamente pelo Swagger UI do FastAPI a partir de um servidor externo. Como a documentação não estará exposta ao público em produção, o risco de um atacante injetar conteúdo malicioso através desse servidor é negligenciável.                             |
| **Threat Model**        | BOLA / IDOR (Leitura indevida de dados de outro médico).                        | API1:2023 - Broken Object Level Authorization                     | Corrigido (Exercício 9): Implementação de Ownership no controlador. Exigência de verificação entre current_user.username e o autor do registo.                                                                                                                                                                                                                                 |
| **Threat Model**        | Mass Assignment (Injeção de campos não previstos).                              | API3:2023 - Broken Object Property Level Auth                     | Corrigido (Exercício 8 e 9): Configuração extra="forbid" no Pydantic V2 e extração do identificador do médico diretamente do token JWT.                                                                                                                                                                                                                                        |

### **Avaliação de Riscos Residuais**

* Ataques de Negação de Serviço Distribuída (DDoS L7): Embora o código conte com a biblioteca Slowapi para aplicar Rate Limiting (mitigando brute-force e credential stuffing de IPs isolados), a aplicação continua suscetível a ataques distribuídos massivos. O limite imposto por IP não impede a exaustão de recursos caso milhares de IPs distintos efetuem pedidos em simultâneo.

### **Parecer de Implantação (Deploy Decision)**

**Decisão: GO (Implantação Aprovada).**

* Riscos Aceitáveis: Os alertas do ZAP refletem apenas limitações do ambiente local (sem TLS) e padrões do Swagger, não indicando falhas lógicas na aplicação.

* Código Seguro: A API de saúde já está blindada internamente contra as vulnerabilidades críticas exigidas (BOLA, BFLA, XSS e Mass Assignment).

* Mitigação em Produção: A proteção contra os riscos residuais (DDoS e TLS) não cabe ao código FastAPI e será delegada à infraestrutura de borda (WAF e API Gateway).