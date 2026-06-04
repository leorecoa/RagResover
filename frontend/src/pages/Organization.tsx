import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Building2, MailPlus, RefreshCw, Save } from "lucide-react";

import {
  getCurrentOrganization,
  inviteOrganizationMember,
  listOrganizationInvitations,
  listOrganizationMembers,
  updateCurrentOrganization,
  updateOrganizationMemberRole,
} from "../lib/api";
import type {
  Organization,
  OrganizationInvitation,
  OrganizationMember,
} from "../lib/types";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { GlassCard } from "../components/ui/GlassCard";
import { Input } from "../components/ui/Input";
import { LoadingState } from "../components/ui/LoadingState";
import { StatusBadge } from "../components/ui/StatusBadge";

interface OrganizationPageProps {
  tenantId?: string;
  apiToken?: string;
}

const roleOptions = ["admin", "member", "viewer"];

export function OrganizationPage({ tenantId, apiToken }: OrganizationPageProps) {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [name, setName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const requestOptions = useMemo(() => ({ tenantId, apiToken }), [apiToken, tenantId]);
  const canManage = organization
    ? ["owner", "admin"].includes(organization.current_user_role)
    : false;
  const canGrantAdmin = organization?.current_user_role === "owner";

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [nextOrganization, nextMembers, nextInvitations] = await Promise.all([
        getCurrentOrganization(requestOptions),
        listOrganizationMembers(requestOptions),
        listOrganizationInvitations(requestOptions).catch(() => ({ invitations: [] })),
      ]);
      setOrganization(nextOrganization);
      setName(nextOrganization.name);
      setMembers(nextMembers.members);
      setInvitations(nextInvitations.invitations);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Organizacao indisponivel.");
    } finally {
      setIsLoading(false);
    }
  }, [requestOptions]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setNotice(null);
    try {
      const updated = await updateCurrentOrganization({ name }, requestOptions);
      setOrganization(updated);
      setName(updated.name);
      setNotice("Organizacao atualizada.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Nao foi possivel salvar.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setNotice(null);
    try {
      const invitation = await inviteOrganizationMember(
        { email: inviteEmail, role: inviteRole },
        requestOptions,
      );
      setInvitations((current) => [invitation, ...current.filter((item) => item.id !== invitation.id)]);
      setInviteEmail("");
      setInviteRole("member");
      setNotice(`Convite criado para ${invitation.email}.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Nao foi possivel convidar.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRoleChange(member: OrganizationMember, role: string) {
    setIsSaving(true);
    setError(null);
    setNotice(null);
    try {
      const response = await updateOrganizationMemberRole(
        member.user_id,
        { role },
        requestOptions,
      );
      const updated = response.members[0];
      setMembers((current) =>
        current.map((item) => (item.user_id === updated.user_id ? updated : item)),
      );
      setNotice(`Role atualizado para ${updated.email}.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Nao foi possivel alterar role.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Carregando organizacao" />;
  }

  return (
    <div className="grid gap-6">
      {error ? <ErrorState title="Organization" message={error} /> : null}
      {notice ? (
        <p className="rounded-md border border-emerald-300/20 bg-emerald-400/10 px-4 py-3 text-sm font-bold text-emerald-100">
          {notice}
        </p>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <GlassCard className="p-5 lg:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 className="text-lg font-black text-white">Organizacao</h2>
              <p className="mt-1 text-sm text-slate-500">{organization?.id}</p>
            </div>
            <StatusBadge
              label={organization?.current_user_role ?? "member"}
              tone={canManage ? "success" : "neutral"}
            />
          </div>

          <form className="mt-5 grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end" onSubmit={handleSave}>
            <label className="field-label">
              Nome da organizacao
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                disabled={!canManage || isSaving}
                aria-label="Nome da organizacao"
              />
            </label>
            <Button
              type="submit"
              disabled={!canManage || isSaving}
              icon={<Save className="h-4 w-4" />}
            >
              Salvar
            </Button>
          </form>
        </GlassCard>

        <GlassCard className="p-5 lg:p-6">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md border border-cyan-300/20 bg-cyan-400/10 text-cyan-100">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white">RBAC</h2>
              <p className="mt-1 text-sm text-slate-500">
                Owner, admin, member e viewer
              </p>
            </div>
          </div>
          <Button
            className="mt-5 w-full"
            variant="secondary"
            onClick={refresh}
            disabled={isSaving}
            icon={<RefreshCw className="h-4 w-4" />}
          >
            Atualizar
          </Button>
        </GlassCard>
      </div>

      <GlassCard className="p-5 lg:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-black text-white">Membros</h2>
            <p className="mt-1 text-sm text-slate-500">Memberships da organizacao atual</p>
          </div>
          <form className="grid gap-3 sm:grid-cols-[minmax(220px,1fr)_140px_auto]" onSubmit={handleInvite}>
            <label className="field-label">
              Email do convite
              <Input
                type="email"
                value={inviteEmail}
                onChange={(event) => setInviteEmail(event.target.value)}
                disabled={!canManage || isSaving}
                required
                aria-label="Email do convite"
              />
            </label>
            <label className="field-label">
              Role
              <select
                className="input-surface"
                value={inviteRole}
                onChange={(event) => setInviteRole(event.target.value)}
                disabled={!canManage || isSaving}
                aria-label="Role do convite"
              >
                {roleOptions
                  .filter((role) => canGrantAdmin || role !== "admin")
                  .map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
              </select>
            </label>
            <Button
              type="submit"
              disabled={!canManage || isSaving}
              icon={<MailPlus className="h-4 w-4" />}
            >
              Convidar
            </Button>
          </form>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[720px] border-separate border-spacing-y-2">
            <thead>
              <tr className="text-left text-xs font-bold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Criado em</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.user_id} className="rounded-md bg-white/[0.04] text-sm text-slate-300">
                  <td className="px-3 py-3">
                    <p className="font-bold text-white">{member.full_name || member.email}</p>
                    <p className="mt-1 text-xs text-slate-500">{member.email}</p>
                  </td>
                  <td className="px-3 py-3">
                    {member.role === "owner" ? (
                      <StatusBadge label="owner" tone="success" />
                    ) : (
                      <select
                        className="input-surface max-w-40"
                        value={member.role}
                        onChange={(event) => handleRoleChange(member, event.target.value)}
                        disabled={!canManage || member.role === "owner" || isSaving}
                        aria-label={`Role de ${member.email}`}
                      >
                        {roleOptions
                          .filter((role) => canGrantAdmin || role !== "admin")
                          .map((role) => (
                            <option key={role} value={role}>
                              {role}
                            </option>
                          ))}
                      </select>
                    )}
                  </td>
                  <td className="px-3 py-3 text-xs text-slate-500">{member.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      <GlassCard className="p-5 lg:p-6">
        <h2 className="text-lg font-black text-white">Convites</h2>
        <div className="mt-4 grid gap-3">
          {invitations.length ? (
            invitations.map((invitation) => (
              <div
                key={invitation.id}
                className="flex flex-col gap-2 rounded-md border border-white/10 bg-white/[0.04] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <p className="text-sm font-bold text-white">{invitation.email}</p>
                  <p className="mt-1 text-xs text-slate-500">{invitation.created_at}</p>
                </div>
                <div className="flex gap-2">
                  <StatusBadge label={invitation.role} />
                  <StatusBadge label={invitation.status} tone="warning" />
                </div>
              </div>
            ))
          ) : (
            <p className="rounded-md border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-500">
              Nenhum convite pendente.
            </p>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
