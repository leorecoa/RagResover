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
  expect(headers.authorization).toBe("Bearer jwt-token");
}

function authUser() {
  return {
    user_id: "11111111-1111-1111-1111-111111111111",
    email: "owner@example.com",
    full_name: "Owner",
    organizations: [
      {
        organization_id: "tenant-alpha",
        role: "owner",
      },
      {
        organization_id: "tenant-beta",
        role: "member",
      },
    ],
  };
}

function authTokenResponse() {
  return {
    access_token: "jwt-token",
    token_type: "bearer",
    expires_in: 3600,
    user: authUser(),
  };
}

async function mockAuthApi(page: Page) {
  await page.route("**/auth/login", async (route) => {
    expect(route.request().postDataJSON()).toMatchObject({
      email: "owner@example.com",
      password: "super-secret",
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(authTokenResponse()),
    });
  });

  await page.route("**/auth/me", async (route) => {
    expectTenantHeaders(route.request());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(authUser()),
    });
  });
}

async function mockOrganizationApi(page: Page) {
  let organizationName = "Acme";
  let memberRole = "member";
  const invitation = {
    id: "invite-1",
    organization_id: "tenant-alpha",
    email: "analyst@example.com",
    role: "viewer",
    invited_by_user_id: "11111111-1111-1111-1111-111111111111",
    status: "pending",
    created_at: "2026-06-04T12:00:00",
  };
  let invitations = [invitation];
  let apiKeys = [
    {
      id: "api-key-1",
      name: "Worker",
      key_prefix: "wrk123",
      role: "member",
      created_by_user_id: "11111111-1111-1111-1111-111111111111",
      created_at: "2026-06-04T12:00:00",
      revoked_at: null,
    },
  ];

  await page.route("**/organizations/current", async (route) => {
    expectTenantHeaders(route.request());
    const request = route.request();
    if (request.method() === "PATCH") {
      const body = request.postDataJSON() as { name: string };
      organizationName = body.name;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "tenant-alpha",
        name: organizationName,
        current_user_role: "owner",
      }),
    });
  });

  await page.route("**/organizations/current/members", async (route) => {
    expectTenantHeaders(route.request());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        members: [
          {
            user_id: "11111111-1111-1111-1111-111111111111",
            email: "owner@example.com",
            full_name: "Owner",
            role: "owner",
            created_at: "2026-06-04T12:00:00",
          },
          {
            user_id: "44444444-4444-4444-4444-444444444444",
            email: "member@example.com",
            full_name: "Member",
            role: memberRole,
            created_at: "2026-06-04T12:05:00",
          },
        ],
      }),
    });
  });

  await page.route("**/organizations/current/members/44444444-4444-4444-4444-444444444444", async (route) => {
    expectTenantHeaders(route.request());
    const body = route.request().postDataJSON() as { role: string };
    memberRole = body.role;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        members: [
          {
            user_id: "44444444-4444-4444-4444-444444444444",
            email: "member@example.com",
            full_name: "Member",
            role: memberRole,
            created_at: "2026-06-04T12:05:00",
          },
        ],
      }),
    });
  });

  await page.route("**/organizations/current/invitations", async (route) => {
    expectTenantHeaders(route.request());
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON() as { email: string; role: string };
      invitations = [
        {
          ...invitation,
          id: "invite-2",
          email: body.email,
          role: body.role,
        },
        ...invitations,
      ];
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(invitations[0]),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ invitations }),
    });
  });

  await page.route("**/organizations/current/api-keys", async (route) => {
    expectTenantHeaders(route.request());
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON() as { name: string; role: string };
      const created = {
        id: "api-key-2",
        name: body.name,
        key_prefix: "new123",
        role: body.role,
        created_by_user_id: "11111111-1111-1111-1111-111111111111",
        created_at: "2026-06-04T12:10:00",
        revoked_at: null,
        api_key: "rrk_new123_secret",
      };
      apiKeys = [created, ...apiKeys];
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(created),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ api_keys: apiKeys }),
    });
  });

  await page.route("**/organizations/current/api-keys/api-key-2", async (route) => {
    expectTenantHeaders(route.request());
    apiKeys = apiKeys.map((apiKey) =>
      apiKey.id === "api-key-2"
        ? { ...apiKey, revoked_at: "2026-06-04T12:15:00" }
        : apiKey,
    );
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        api_keys: [apiKeys.find((apiKey) => apiKey.id === "api-key-2")],
      }),
    });
  });
}

async function signIn(page: Page) {
  await page.goto("/");
  await page.getByLabel("Email").fill("owner@example.com");
  await page.getByLabel("Senha").fill("super-secret");
  await page.getByRole("button", { name: "Entrar" }).click();
}

function uploadJob(overrides: Record<string, unknown> = {}) {
  return {
    job_id: "job-upload-1",
    filename: "policy.pdf",
    content_type: "application/pdf",
    file_size: 2048,
    status: "pending",
    tenant_id: "tenant-alpha",
    error_message: null,
    attempts: 0,
    max_attempts: 3,
    last_error: null,
    document_id: null,
    created_at: "2026-06-03T12:00:00",
    updated_at: "2026-06-03T12:00:00",
    started_at: null,
    finished_at: null,
    message: "Upload recebido para processamento.",
    ...overrides,
  };
}

test.beforeEach(async ({ page }) => {
  await mockBaseApi(page);
  await mockAuthApi(page);
  await mockOrganizationApi(page);
});

test("renders dashboard status and global tenant controls", async ({ page }) => {
  await signIn(page);

  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByText("healthy").first()).toBeVisible();
  await expect(page.getByText("ready").first()).toBeVisible();
  await expect(page.getByText("database available")).toBeVisible();
  await expect(page.getByLabel("Organizacao atual")).toHaveValue("tenant-alpha");
  await expect(page.getByText("owner - JWT ativo")).toBeVisible();
});

test("uploads a document with tenant and token headers", async ({ page }) => {
  let statusCalls = 0;

  await page.route("**/upload", async (route) => {
    expectTenantHeaders(route.request());
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(uploadJob()),
    });
  });

  await page.route("**/uploads?**", async (route) => {
    expectTenantHeaders(route.request());
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        uploads: [],
        limit: 10,
        offset: 0,
        count: 0,
      }),
    });
  });

  await page.route("**/uploads/job-upload-1", async (route) => {
    expectTenantHeaders(route.request());
    statusCalls += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(uploadJob({
        status: statusCalls > 1 ? "completed" : "processing",
        attempts: 1,
        document_id: statusCalls > 1 ? "doc-upload-1" : null,
        updated_at: "2026-06-03T12:00:01",
        started_at: "2026-06-03T12:00:01",
        finished_at: statusCalls > 1 ? "2026-06-03T12:00:03" : null,
      })),
    });
  });

  await signIn(page);
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
  await expect(page.getByText("1/3").first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Abrir Documents" })).toBeVisible();
  expect(statusCalls).toBeGreaterThan(1);
});

test("manages upload job history with filters, retry and cancel", async ({ page }) => {
  let sawFilteredRequest = false;
  let retryCalled = false;
  let cancelCalled = false;

  await page.route("**/uploads/job-failed/retry", async (route) => {
    expectTenantHeaders(route.request());
    retryCalled = true;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(uploadJob({
        job_id: "job-failed",
        filename: "failed.pdf",
        status: "pending",
        attempts: 0,
        last_error: "Arquivo PDF invalido.",
        message: "Upload job reenfileirado para processamento.",
      })),
    });
  });

  await page.route("**/uploads/job-pending/cancel", async (route) => {
    expectTenantHeaders(route.request());
    cancelCalled = true;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(uploadJob({
        job_id: "job-pending",
        filename: "pending.docx",
        content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        status: "canceled",
        error_message: "Upload cancelado pelo usuario.",
        message: "Upload job cancelado.",
      })),
    });
  });

  await page.route("**/uploads?**", async (route) => {
    expectTenantHeaders(route.request());
    const url = new URL(route.request().url());
    if (url.searchParams.get("status") === "failed") {
      sawFilteredRequest = true;
      expect(url.searchParams.get("filename")).toBe("failed");
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        uploads: [
          uploadJob({
            job_id: "job-failed",
            filename: "failed.pdf",
            status: "failed",
            attempts: 3,
            error_message: "Arquivo PDF invalido.",
            last_error: "Arquivo PDF invalido.",
            finished_at: "2026-06-03T12:04:00",
          }),
          uploadJob({
            job_id: "job-pending",
            filename: "pending.docx",
            content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            status: "pending",
            attempts: 0,
          }),
        ],
        limit: 10,
        offset: 0,
        count: 2,
      }),
    });
  });

  await signIn(page);
  await page.getByRole("button", { name: /Upload Ingestao/ }).click();

  await expect(
    page.getByRole("heading", { name: "Upload jobs", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("failed.pdf")).toBeVisible();
  await expect(page.getByText("pending.docx")).toBeVisible();
  await expect(page.getByText("Arquivo PDF invalido.").first()).toBeVisible();

  await page.getByLabel("Filtro por status de upload").selectOption("failed");
  await page.getByLabel("Filtro por filename de upload").fill("failed");
  await page.getByRole("button", { name: "Filtrar uploads" }).click();
  expect(sawFilteredRequest).toBe(true);

  await page.getByRole("button", { name: "Retry failed.pdf" }).click();
  await expect(page.getByText("Job reenfileirado: failed.pdf")).toBeVisible();
  expect(retryCalled).toBe(true);

  await page.getByRole("button", { name: "Cancel pending.docx" }).click();
  await expect(page.getByText("Job cancelado: pending.docx")).toBeVisible();
  expect(cancelCalled).toBe(true);
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

  await signIn(page);
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

  await signIn(page);
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

  await signIn(page);
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

test("manages organization settings, invites and member roles", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: /Organization B2B admin/ }).click();

  await expect(page.getByRole("heading", { name: "Organization" }).first()).toBeVisible();
  await expect(page.getByLabel("Nome da organizacao")).toHaveValue("Acme");

  await page.getByLabel("Nome da organizacao").fill("Acme Legal");
  await page.getByRole("button", { name: "Salvar" }).click();
  await expect(page.getByText("Organizacao atualizada.")).toBeVisible();

  await page.getByLabel("Email do convite").fill("new.member@example.com");
  await page.getByLabel("Role do convite").selectOption("viewer");
  await page.getByRole("button", { name: "Convidar" }).click();
  await expect(page.getByText("Convite criado para new.member@example.com.")).toBeVisible();
  await expect(page.getByText("new.member@example.com", { exact: true })).toBeVisible();

  await page.getByLabel("Role de member@example.com").selectOption("viewer");
  await expect(page.getByText("Role atualizado para member@example.com.")).toBeVisible();

  await page.getByLabel("Nome da API key").fill("Search Worker");
  await page.getByLabel("Role da API key").selectOption("viewer");
  await page.getByRole("button", { name: "Criar key" }).click();
  await expect(page.getByText("API key criada: Search Worker.")).toBeVisible();
  await expect(page.getByText("rrk_new123_secret")).toBeVisible();
  await expect(page.getByText("prefix new123")).toBeVisible();

  await page.getByRole("button", { name: "Revogar" }).first().click();
  await expect(page.getByText("API key revogada: Search Worker.")).toBeVisible();
});
