import { expect, test, type Page, type Request } from "@playwright/test";

async function mockBaseApi(page: Page) {
  await page.route("**/health", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "healthy",
        env: "test",
        version: "e2e",
      }),
    });
  });

  await page.route("**/ready", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ready",
        database: "available",
        storage: "available",
        env: "test",
        version: "e2e",
      }),
    });
  });
}

function expectTenantHeaders(request: Request) {
  const headers = request.headers();
  expect(headers["x-tenant-id"]).toBe("tenant-alpha");
  expect(headers.authorization).toBe("Bearer demo-token");
}

test.beforeEach(async ({ page }) => {
  await mockBaseApi(page);
});

test("renders dashboard status and global tenant controls", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("healthy").first()).toBeVisible();
  await expect(page.getByText("ready").first()).toBeVisible();
  await expect(page.getByText("database available")).toBeVisible();
  await expect(page.getByLabel("Tenant ID")).toHaveValue("tenant-demo");
});

test("uploads a document with tenant and token headers", async ({ page }) => {
  let statusCalls = 0;

  await page.route("**/upload", async (route) => {
    expectTenantHeaders(route.request());
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "job-upload-1",
        filename: "policy.pdf",
        content_type: "application/pdf",
        file_size: 2048,
        status: "pending",
        tenant_id: "tenant-alpha",
        error_message: null,
        document_id: null,
        created_at: "2026-06-03T12:00:00",
        updated_at: "2026-06-03T12:00:00",
        message: "Upload recebido para processamento.",
      }),
    });
  });

  await page.route("**/uploads/job-upload-1", async (route) => {
    expectTenantHeaders(route.request());
    statusCalls += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "job-upload-1",
        filename: "policy.pdf",
        content_type: "application/pdf",
        file_size: 2048,
        status: statusCalls > 1 ? "completed" : "processing",
        tenant_id: "tenant-alpha",
        error_message: null,
        document_id: statusCalls > 1 ? "doc-upload-1" : null,
        created_at: "2026-06-03T12:00:00",
        updated_at: "2026-06-03T12:00:01",
        message: "Upload recebido para processamento.",
      }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Tenant ID").fill("tenant-alpha");
  await page.getByLabel("API token").fill("demo-token");
  await page.getByRole("button", { name: /Upload Ingestao/ }).click();

  await page.getByLabel("Selecionar arquivo").setInputFiles({
    name: "policy.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\n% e2e fixture\n"),
  });
  await page.getByRole("button", { name: "Indexar documento" }).click();

  await expect(page.getByText("Upload completed")).toBeVisible();
  await expect(page.getByText("policy.pdf").first()).toBeVisible();
  await expect(page.getByText("completed").first()).toBeVisible();
  await expect(page.getByText("doc-upload-1").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Abrir Documents" })).toBeVisible();
  expect(statusCalls).toBeGreaterThan(1);
});

test("manages documents with details, chunks, filters and delete", async ({ page }) => {
  let deleteCalled = false;
  let sawFilteredRequest = false;

  await page.route("**/documents**", async (route) => {
    expectTenantHeaders(route.request());
    const request = route.request();
    const url = new URL(request.url());

    if (request.method() === "GET" && url.pathname === "/documents") {
      if ((url.searchParams.get("source") ?? "") === "manual") {
        sawFilteredRequest = true;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          documents: deleteCalled
            ? []
            : [
                {
                  id: "11111111-1111-1111-1111-111111111111",
                  file_name: "manual.pdf",
                  content_type: "application/pdf",
                  file_size: 2048,
                  chunks_count: 2,
                  tenant_id: "tenant-alpha",
                  created_at: "2026-06-01T12:00:00",
                  metadata: {
                    source: "manual.pdf",
                    page_count: 4,
                  },
                },
              ],
        }),
      });
      return;
    }

    if (request.method() === "GET" && url.pathname.endsWith("/chunks")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: "11111111-1111-1111-1111-111111111111",
          page: 1,
          page_size: 20,
          total: 2,
          chunks: [
            {
              id: "22222222-2222-2222-2222-222222222222",
              document_id: "11111111-1111-1111-1111-111111111111",
              chunk_index: 0,
              content: "Retention window is 180 days.",
              metadata: {
                source: "manual.pdf",
                page: 1,
              },
              created_at: "2026-06-01T12:01:00",
            },
          ],
        }),
      });
      return;
    }

    if (request.method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "11111111-1111-1111-1111-111111111111",
          file_name: "manual.pdf",
          content_type: "application/pdf",
          file_size: 2048,
          chunks_count: 2,
          tenant_id: "tenant-alpha",
          created_at: "2026-06-01T12:00:00",
          metadata: {
            source: "manual.pdf",
            page_count: 4,
          },
        }),
      });
      return;
    }

    if (request.method() === "DELETE") {
      deleteCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          document_id: "11111111-1111-1111-1111-111111111111",
          status: "deleted",
          message: "Documento e chunks removidos.",
        }),
      });
      return;
    }

    await route.fallback();
  });

  await page.goto("/");
  await page.getByLabel("Tenant ID").fill("tenant-alpha");
  await page.getByLabel("API token").fill("demo-token");
  await page.getByRole("button", { name: /Documents Library/ }).click();

  await expect(page.getByRole("heading", { name: "Documents" }).first()).toBeVisible();
  await expect(page.getByText("manual.pdf").first()).toBeVisible();
  await expect(page.getByText("application/pdf").first()).toBeVisible();
  await expect(page.getByText("Retention window is 180 days.")).toBeVisible();
  await expect(page.getByText("source: manual.pdf")).toBeVisible();
  await expect(page.getByText("page_count")).toBeVisible();

  await page.getByLabel("Filtrar por source").fill("manual");
  await page.getByRole("button", { name: "Filtrar documentos" }).click();
  await expect(page.getByText("manual.pdf").first()).toBeVisible();
  expect(sawFilteredRequest).toBe(true);

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("manual.pdf");
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Delete" }).click();

  await expect(page.getByText("manual.pdf removido.")).toBeVisible();
  await expect(page.getByText("Sem documentos")).toBeVisible();
  expect(deleteCalled).toBe(true);
});

test("runs semantic search with retrieval controls and diagnostics", async ({ page }) => {
  let capturedBody: unknown;

  await page.route("**/search", async (route) => {
    expectTenantHeaders(route.request());
    capturedBody = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        query: "retention policy",
        results: [
          {
            chunk_id: "chunk-1",
            document_id: "doc-1",
            file_name: "manual.pdf",
            content: "Retention window is 180 days for tenant alpha.",
            score: 0.92,
            metadata: {
              source: "manual.pdf",
              content_type: "application/pdf",
              page: 2,
              page_count: 4,
            },
          },
        ],
        diagnostics: {
          requested_top_k: 7,
          fetch_limit: 28,
          returned_count: 1,
          tenant_id: "tenant-alpha",
          score_threshold: 0.5,
          metadata_filters: { source: "manual.pdf" },
          embedding_provider: "ollama",
          reranker_provider: "none",
          reranker_applied: false,
        },
      }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Tenant ID").fill("tenant-alpha");
  await page.getByLabel("API token").fill("demo-token");
  await page.getByRole("button", { name: /Search Retrieval/ }).click();

  await page.getByLabel("Consulta de busca semantica").fill("retention policy");
  await page.getByLabel("Quantidade de resultados").fill("7");
  await page.getByLabel("Score threshold").fill("0.5");
  await page.getByLabel("Filtro por source").fill("manual.pdf");
  await page.getByRole("button", { name: "Buscar" }).click();

  await expect(page.getByText("manual.pdf").first()).toBeVisible();
  await expect(page.getByText("Retention window is 180 days for tenant alpha.")).toBeVisible();
  await expect(page.getByText("score 0.920")).toBeVisible();
  await expect(page.getByText("provider ollama")).toBeVisible();
  await expect(page.getByText("tenant tenant-alpha")).toBeVisible();

  expect(capturedBody).toEqual({
    query: "retention policy",
    top_k: 7,
    score_threshold: 0.5,
    metadata_filters: { source: "manual.pdf" },
  });
});

test("asks chat and renders grounded answer with source metadata", async ({ page }) => {
  let capturedBody: unknown;

  await page.route("**/chat", async (route) => {
    expectTenantHeaders(route.request());
    capturedBody = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        question: "What is the retention window?",
        answer: "The retention window is 180 days [1].",
        sources: [
          {
            index: 1,
            chunk_id: "chunk-chat-1",
            document_id: "doc-1",
            file_name: "manual.pdf",
            score: 0.94,
            excerpt: "Retention window is 180 days for tenant alpha.",
            metadata: {
              source: "manual.pdf",
              content_type: "application/pdf",
              page: 2,
              paragraph: 5,
            },
          },
        ],
        diagnostics: {
          requested_top_k: 4,
          fetch_limit: 16,
          returned_count: 1,
          tenant_id: "tenant-alpha",
          score_threshold: 0.2,
          metadata_filters: { source: "manual.pdf" },
          embedding_provider: "ollama",
          reranker_provider: "none",
          reranker_applied: false,
        },
      }),
    });
  });

  await page.goto("/");
  await page.getByLabel("Tenant ID").fill("tenant-alpha");
  await page.getByLabel("API token").fill("demo-token");
  await page.getByRole("button", { name: /Chat RAG/ }).click();

  await page.getByLabel("Quantidade de fontes").fill("4");
  await page.getByLabel("Score threshold do chat").fill("0.2");
  await page.getByLabel("Filtro de source do chat").fill("manual.pdf");
  await page.getByLabel("Pergunta para o chat").fill("What is the retention window?");
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByText("What is the retention window?")).toBeVisible();
  await expect(page.getByText("The retention window is 180 days [1].")).toBeVisible();
  await expect(page.getByText("[1] manual.pdf")).toBeVisible();
  await expect(page.getByText("page 2")).toBeVisible();
  await expect(page.getByText("paragraph 5")).toBeVisible();
  await expect(page.getByText("provider ollama")).toBeVisible();

  expect(capturedBody).toEqual({
    question: "What is the retention window?",
    top_k: 4,
    score_threshold: 0.2,
    metadata_filters: { source: "manual.pdf" },
  });
});
