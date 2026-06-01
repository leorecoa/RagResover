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
- [x] Criar suite inicial de testes automatizados sem depender de Docker/provedores externos
- [x] Criar migrations iniciais com Alembic e servico Docker de migracao

## Proximas tarefas

- [ ] Adicionar reranking opcional com Cohere
- [ ] Adicionar parsers reais para PDF, DOCX e HTML
- [ ] Ampliar cobertura de testes com casos de integracao e banco real
- [ ] Endurecer workflow de migrations com testes de banco real e downgrade smoke test
- [ ] Evoluir frontend para Next.js/React se precisar de estado mais complexo
- [ ] Adicionar autenticacao e separacao por usuario/tenant
- [ ] Adicionar observabilidade mais completa

## Riscos tecnicos atuais

- Upload ainda le o arquivo inteiro em memoria.
- Sem `OPENAI_API_KEY`, os chunks sao salvos sem embedding.
- O banco precisa estar inicializado com `scripts/init_db.sql`.
- O fluxo de chat inicial existe, mas ainda precisa de testes, reranking e melhor controle de fontes.
