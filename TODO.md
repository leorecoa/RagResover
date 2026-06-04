# TODO - RagResover MVP RAG

## Concluido

- [x] Criar backend FastAPI modular
- [x] Separar core, rotas, schemas, services, repository e db
- [x] Criar configuracao por `.env`
- [x] Criar logging basico
- [x] Criar CORS configuravel
- [x] Criar upload de documentos
- [x] Validar tipo, nome, tamanho e conteudo vazio no upload
- [x] Salvar arquivo bruto no MinIO
- [x] Fazer chunking com LangChain
- [x] Criar schema PostgreSQL com pgvector
- [x] Persistir documento fonte e chunks no Postgres
- [x] Gerar embeddings com OpenAI quando `OPENAI_API_KEY` existir
- [x] Suportar Ollama local para chat e embeddings
- [x] Salvar embeddings em `document_chunks.embedding`
- [x] Criar busca semantica em `/search`
- [x] Criar endpoint `/chat` usando retrieval + LLM
- [x] Criar prompt builder inicial com fontes citadas
- [x] Criar `/health` e `/ready`
- [x] Criar Dockerfile e Docker Compose com Postgres, Redis e MinIO
- [x] Criar frontend estatico inicial para upload, busca e chat
- [x] Criar documentacao inicial para arquitetura, API, seguranca, deploy e prontidao comercial
- [x] Fixar versoes diretas em `requirements.txt`
- [x] Criar workflow de CI e script local de validacao
- [x] Criar suite inicial de testes automatizados com pytest sem depender de Docker/provedores externos
- [x] Criar migrations iniciais com Alembic e servico Docker de migracao
- [x] Adicionar parsers reais para PDF e DOCX com metadados de pagina/secao
- [x] Adicionar controles de retrieval com threshold, filtros, diagnostics e reranker placeholder
- [x] Adicionar autenticacao MVP e isolamento por tenant em upload/search/chat

## Proximas tarefas

- [x] Implementar reranking real com Cohere ou provider compativel
- [x] Adicionar parser HTML com metadados de titulo/secao
- [ ] Adicionar OCR para PDFs escaneados
- [x] Adicionar testes opcionais de integracao com banco real
- [x] Adicionar smoke test offline de downgrade no workflow local de migrations
- [ ] Endurecer workflow de migrations com testes de banco real
- [ ] Evoluir frontend para Next.js/React se precisar de estado mais complexo
- [x] Adicionar contexto MVP de usuario/roles e gate admin para metricas
- [x] Adicionar auditoria persistente para upload e documentos
- [x] Adicionar backend auth real com JWT, usuarios, organizacoes e memberships
- [x] Adicionar UI de login e selecao de organizacao atual
- [x] Adicionar settings de organizacao, convites pendentes e RBAC MVP
- [ ] Adicionar API keys por tenant, aceite/envio de convites e RBAC completo
- [x] Adicionar request id, logs de duracao por request e endpoint `/metrics`
- [x] Adicionar propagacao W3C `traceparent` para traces distribuidos opcionais

## Riscos tecnicos atuais

- Upload faz leitura em chunks com limite antecipado, mas ainda materializa bytes para storage/parsing.
- Sem `OPENAI_API_KEY`, os chunks sao salvos sem embedding.
- O banco precisa estar inicializado com `scripts/init_db.sql`.
- O fluxo de chat inicial existe, mas ainda precisa de melhor avaliacao de qualidade.
