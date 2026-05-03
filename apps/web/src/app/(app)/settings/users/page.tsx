"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Pencil, Plus, ShieldCheck, Trash2, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { extractApiError } from "@/lib/api-client";
import { departmentsApi, rolesApi, usersApi } from "@/lib/tenant-api";
import type {
  Department,
  InviteUserPayload,
  InvitedUser,
  Role,
  RoleCreatePayload,
  User,
} from "@/lib/types";

export default function UsersPage() {
  const qc = useQueryClient();
  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: usersApi.list });
  const { data: roles = [] } = useQuery({ queryKey: ["roles"], queryFn: rolesApi.list });
  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.list,
  });
  const { data: knownPermissions = [] } = useQuery({
    queryKey: ["roles-permissions"],
    queryFn: rolesApi.knownPermissions,
  });

  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteResult, setInviteResult] = useState<InvitedUser | null>(null);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [editRole, setEditRole] = useState<Role | null>(null);
  const [createRoleOpen, setCreateRoleOpen] = useState(false);

  const remove = useMutation({
    mutationFn: usersApi.remove,
    onSuccess: () => {
      toast.success("Xodim olib tashlandi");
      qc.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const removeRole = useMutation({
    mutationFn: rolesApi.remove,
    onSuccess: () => {
      toast.success("Rol o'chirildi");
      qc.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Xodimlar ({users.length})</CardTitle>
          <Button onClick={() => setInviteOpen(true)}>
            <Plus className="h-4 w-4" /> Taklif qilish
          </Button>
        </CardHeader>
        <CardContent>
          {users.length === 0 ? (
            <p className="text-muted text-sm">Xodim yo&apos;q</p>
          ) : (
            <ul className="border-cream-200 divide-cream-200 divide-y rounded-md border">
              {users.map((u) => (
                <li
                  key={u.id}
                  className="bg-cream flex items-center justify-between px-3 py-3 text-sm first:rounded-t-md last:rounded-b-md"
                >
                  <div className="min-w-0">
                    <p className="text-charcoal truncate">{u.full_name ?? u.email}</p>
                    <p className="text-muted truncate text-xs">{u.email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-gold/10 text-gold-deep rounded-full px-2 py-0.5 text-xs">
                      {u.role}
                    </span>
                    <button
                      type="button"
                      aria-label="Tahrirlash"
                      onClick={() => setEditUser(u)}
                      className="hover:bg-cream-200 rounded p-1.5"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    {u.role !== "owner" ? (
                      <button
                        type="button"
                        aria-label="O'chirish"
                        onClick={() => {
                          if (
                            window.confirm(
                              `${u.email} ni olib tashlashga ishonchingiz komilmi?`,
                            )
                          ) {
                            remove.mutate(u.id);
                          }
                        }}
                        className="text-destructive hover:bg-destructive/10 rounded p-1.5"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Rollar ({roles.length})</CardTitle>
          <Button variant="outline" onClick={() => setCreateRoleOpen(true)}>
            <Plus className="h-4 w-4" /> Yangi rol
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2">
            {roles.map((r) => (
              <div
                key={r.id}
                className="border-cream-200 bg-cream flex items-start justify-between rounded-md border p-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{r.name}</p>
                    {r.is_system ? (
                      <span className="bg-charcoal text-cream rounded px-1.5 py-0.5 text-[10px]">
                        tizim
                      </span>
                    ) : null}
                  </div>
                  <p className="text-muted mt-1 text-xs">{r.description}</p>
                  <p className="text-muted mt-2 text-xs">{r.permissions.length} ta imtiyoz</p>
                </div>
                {!r.is_system ? (
                  <div className="flex shrink-0 gap-1">
                    <button
                      type="button"
                      aria-label="Rolni tahrirlash"
                      onClick={() => setEditRole(r)}
                      className="hover:bg-cream-200 rounded p-1.5"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      aria-label="Rolni o'chirish"
                      onClick={() => {
                        if (window.confirm(`${r.name} rolini o'chirishni istaysizmi?`)) {
                          removeRole.mutate(r.id);
                        }
                      }}
                      className="text-destructive hover:bg-destructive/10 rounded p-1.5"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {inviteOpen ? (
        <InviteModal
          roles={roles}
          departments={departments}
          onCancel={() => setInviteOpen(false)}
          onCreated={(user) => {
            setInviteResult(user);
            setInviteOpen(false);
            qc.invalidateQueries({ queryKey: ["users"] });
          }}
        />
      ) : null}

      {inviteResult ? (
        <InvitedNotice user={inviteResult} onClose={() => setInviteResult(null)} />
      ) : null}

      {editUser ? (
        <EditUserModal
          user={editUser}
          roles={roles}
          departments={departments}
          onCancel={() => setEditUser(null)}
          onSaved={() => {
            setEditUser(null);
            qc.invalidateQueries({ queryKey: ["users"] });
          }}
        />
      ) : null}

      {editRole || createRoleOpen ? (
        <RoleEditorModal
          role={editRole}
          knownPermissions={knownPermissions}
          onCancel={() => {
            setEditRole(null);
            setCreateRoleOpen(false);
          }}
          onSaved={() => {
            setEditRole(null);
            setCreateRoleOpen(false);
            qc.invalidateQueries({ queryKey: ["roles"] });
          }}
        />
      ) : null}
    </div>
  );
}

function InviteModal({
  roles,
  departments,
  onCancel,
  onCreated,
}: {
  roles: Role[];
  departments: Department[];
  onCancel: () => void;
  onCreated: (user: InvitedUser) => void;
}) {
  const [form, setForm] = useState<InviteUserPayload>({
    email: "",
    phone: "+998",
    full_name: "",
    role_slug: roles.find((r) => r.slug !== "owner")?.slug ?? "operator",
    department_id: null,
  });

  const submit = useMutation({
    mutationFn: () => usersApi.invite(form),
    onSuccess: onCreated,
    onError: (e) => toast.error(extractApiError(e)),
  });

  return (
    <ModalShell title="Xodim taklif qilish" onCancel={onCancel}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit.mutate();
        }}
      >
        <FormField label="To'liq ism">
          <Input
            value={form.full_name ?? ""}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
        </FormField>
        <FormField label="Email" required>
          <Input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Telefon" hint="+998 prefiksi bilan" required>
          <Input
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            required
          />
        </FormField>
        <FormField label="Rol" required>
          <select
            value={form.role_slug}
            onChange={(e) => setForm({ ...form, role_slug: e.target.value })}
            className="border-cream-200 focus:border-gold focus:ring-gold/20 w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-2 focus:outline-none"
          >
            {roles
              .filter((r) => r.slug !== "owner")
              .map((r) => (
                <option key={r.id} value={r.slug}>
                  {r.name}
                </option>
              ))}
          </select>
        </FormField>
        <FormField label="Bo'lim">
          <select
            value={form.department_id ?? ""}
            onChange={(e) => setForm({ ...form, department_id: e.target.value || null })}
            className="border-cream-200 focus:border-gold focus:ring-gold/20 w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-2 focus:outline-none"
          >
            <option value="">— tanlanmagan —</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </FormField>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button type="submit" loading={submit.isPending}>
            Yaratish
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function InvitedNotice({ user, onClose }: { user: InvitedUser; onClose: () => void }) {
  return (
    <ModalShell title="Vaqtinchalik parol" onCancel={onClose}>
      <div className="space-y-3 text-sm">
        <p>
          <b>{user.email}</b> uchun akkaunt yaratildi. Vaqtinchalik parolni xodimga xavfsiz
          kanal orqali yuboring — birinchi kirishdan keyin uni o&apos;zgartirish tavsiya
          etiladi.
        </p>
        <code className="bg-cream-100 block rounded-md px-3 py-2 text-base">
          {user.temporary_password}
        </code>
        <div className="flex justify-end pt-2">
          <Button onClick={onClose}>Tushundim</Button>
        </div>
      </div>
    </ModalShell>
  );
}

function EditUserModal({
  user,
  roles,
  departments,
  onCancel,
  onSaved,
}: {
  user: User;
  roles: Role[];
  departments: Department[];
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [fullName, setFullName] = useState(user.full_name ?? "");
  const [roleSlug, setRoleSlug] = useState(user.role);
  const [departmentId, setDepartmentId] = useState<string>("");

  const save = useMutation({
    mutationFn: () =>
      usersApi.update(user.id, {
        full_name: fullName,
        role_slug: roleSlug,
        department_id: departmentId || null,
      }),
    onSuccess: () => {
      toast.success("Saqlandi");
      onSaved();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  const isOwner = user.role === "owner";

  return (
    <ModalShell title="Xodimni tahrirlash" onCancel={onCancel}>
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <FormField label="To'liq ism">
          <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </FormField>
        <FormField label="Rol">
          <select
            value={roleSlug}
            disabled={isOwner}
            onChange={(e) => setRoleSlug(e.target.value)}
            className="border-cream-200 focus:border-gold focus:ring-gold/20 w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-2 focus:outline-none disabled:opacity-50"
          >
            {roles.map((r) => (
              <option key={r.id} value={r.slug}>
                {r.name}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Bo'lim">
          <select
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
            className="border-cream-200 focus:border-gold focus:ring-gold/20 w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-2 focus:outline-none"
          >
            <option value="">— tanlanmagan —</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </FormField>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button type="submit" loading={save.isPending}>
            Saqlash
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function RoleEditorModal({
  role,
  knownPermissions,
  onCancel,
  onSaved,
}: {
  role: Role | null;
  knownPermissions: string[];
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(role?.name ?? "");
  const [description, setDescription] = useState(role?.description ?? "");
  const [permissions, setPermissions] = useState<string[]>(role?.permissions ?? []);

  const isEdit = role !== null;

  const save = useMutation({
    mutationFn: () => {
      if (isEdit && role) {
        return rolesApi.update(role.id, { name, description, permissions });
      }
      const payload: RoleCreatePayload = { name, description, permissions };
      return rolesApi.create(payload);
    },
    onSuccess: () => {
      toast.success(isEdit ? "Rol yangilandi" : "Rol yaratildi");
      onSaved();
    },
    onError: (e) => toast.error(extractApiError(e)),
  });

  function toggle(perm: string) {
    setPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm],
    );
  }

  const grouped = knownPermissions.reduce<Record<string, string[]>>((acc, p) => {
    const [resource] = p.split(".");
    (acc[resource] ??= []).push(p);
    return acc;
  }, {});

  return (
    <ModalShell
      title={isEdit ? `${role?.name} rolini tahrirlash` : "Yangi rol"}
      onCancel={onCancel}
      wide
    >
      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <FormField label="Nomi" required>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </FormField>
        <FormField label="Tavsif">
          <Input value={description ?? ""} onChange={(e) => setDescription(e.target.value)} />
        </FormField>
        <div>
          <p className="mb-2 flex items-center gap-2 text-sm font-medium">
            <ShieldCheck className="h-4 w-4" /> Imtiyozlar ({permissions.length}/
            {knownPermissions.length})
          </p>
          <div className="border-cream-200 max-h-72 overflow-y-auto rounded-md border p-3">
            {Object.entries(grouped).map(([resource, perms]) => (
              <div key={resource} className="mb-3 last:mb-0">
                <p className="text-muted mb-1 text-xs font-semibold tracking-wide uppercase">
                  {resource}
                </p>
                <div className="grid gap-1 sm:grid-cols-2">
                  {perms.map((perm) => (
                    <label
                      key={perm}
                      className="hover:bg-cream-100 flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-xs"
                    >
                      <input
                        type="checkbox"
                        checked={permissions.includes(perm)}
                        onChange={() => toggle(perm)}
                      />
                      <span className="font-mono">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Bekor qilish
          </Button>
          <Button type="submit" loading={save.isPending}>
            Saqlash
          </Button>
        </div>
      </form>
    </ModalShell>
  );
}

function ModalShell({
  title,
  children,
  onCancel,
  wide,
}: {
  title: string;
  children: React.ReactNode;
  onCancel: () => void;
  wide?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.18 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.96, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.18 }}
        onClick={(e) => e.stopPropagation()}
        className={`bg-cream w-full ${wide ? "max-w-2xl" : "max-w-md"} border-cream-200 rounded-xl border shadow-xl`}
      >
        <div className="border-cream-200 flex items-center justify-between border-b px-5 py-4">
          <h3 className="text-charcoal text-base font-semibold">{title}</h3>
          <button
            type="button"
            aria-label="Yopish"
            onClick={onCancel}
            className="text-muted hover:bg-cream-200 rounded-md p-1"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </motion.div>
    </motion.div>
  );
}
