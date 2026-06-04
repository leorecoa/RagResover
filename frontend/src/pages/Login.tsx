import { FormEvent, useState } from "react";
import { LogIn, UserPlus } from "lucide-react";

import { ApiError, login, register } from "../lib/api";
import type { AuthTokenResponse } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

interface LoginPageProps {
  onAuthenticated: (response: AuthTokenResponse) => void;
}

type AuthMode = "login" | "register";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Nao foi possivel autenticar.";
}

export function LoginPage({ onAuthenticated }: LoginPageProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = isRegister
        ? await register({
            email,
            password,
            full_name: fullName.trim() || null,
            organization_name: organizationName,
          })
        : await login({
            email,
            password,
            organization_id: organizationId.trim() || null,
          });
      onAuthenticated(response);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-4 py-8">
      <section className="w-full max-w-md rounded-lg border border-white/10 bg-slate-950/72 p-6 shadow-glow backdrop-blur-2xl">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-md border border-cyan-300/20 bg-cyan-400/10 text-cyan-200">
            {isRegister ? <UserPlus className="h-5 w-5" /> : <LogIn className="h-5 w-5" />}
          </div>
          <div>
            <p className="text-sm font-black uppercase tracking-[0.18em] text-cyan-100">
              RagResover
            </p>
            <h1 className="mt-1 text-xl font-black text-white">
              {isRegister ? "Criar organizacao" : "Entrar"}
            </h1>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-2 rounded-md border border-white/10 bg-white/[0.04] p-1">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`min-h-10 rounded-md text-sm font-bold transition ${
              mode === "login" ? "bg-cyan-300 text-slate-950" : "text-slate-300"
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`min-h-10 rounded-md text-sm font-bold transition ${
              mode === "register" ? "bg-cyan-300 text-slate-950" : "text-slate-300"
            }`}
          >
            Registro
          </button>
        </div>

        <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
          <label className="field-label">
            Email
            <Input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              aria-label="Email"
            />
          </label>

          <label className="field-label">
            Senha
            <Input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              minLength={8}
              required
              aria-label="Senha"
            />
          </label>

          {isRegister ? (
            <>
              <label className="field-label">
                Nome
                <Input
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  autoComplete="name"
                  aria-label="Nome"
                />
              </label>
              <label className="field-label">
                Organizacao
                <Input
                  value={organizationName}
                  onChange={(event) => setOrganizationName(event.target.value)}
                  required
                  aria-label="Organizacao"
                />
              </label>
            </>
          ) : (
            <label className="field-label">
              Organizacao opcional
              <Input
                value={organizationId}
                onChange={(event) => setOrganizationId(event.target.value)}
                placeholder="UUID quando necessario"
                aria-label="Organizacao opcional"
              />
            </label>
          )}

          {error ? (
            <p className="rounded-md border border-rose-300/20 bg-rose-500/10 px-3 py-2 text-sm font-semibold text-rose-100">
              {error}
            </p>
          ) : null}

          <Button type="submit" disabled={isSubmitting} icon={isRegister ? <UserPlus className="h-4 w-4" /> : <LogIn className="h-4 w-4" />}>
            {isSubmitting ? "Autenticando..." : isRegister ? "Criar conta" : "Entrar"}
          </Button>
        </form>
      </section>
    </main>
  );
}
