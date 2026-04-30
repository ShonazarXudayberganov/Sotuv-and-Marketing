import { apiClient } from "./api-client";
import type {
  Department,
  DepartmentCreate,
  OnboardingState,
  Role,
  Tenant,
  User,
} from "./types";

export const tenantApi = {
  async me(): Promise<Tenant> {
    const { data } = await apiClient.get<Tenant>("/tenant/me");
    return data;
  },
  async update(payload: { name?: string; industry?: string }): Promise<Tenant> {
    const { data } = await apiClient.patch<Tenant>("/tenant/me", payload);
    return data;
  },
};

export const departmentsApi = {
  async list(): Promise<Department[]> {
    const { data } = await apiClient.get<Department[]>("/departments");
    return data;
  },
  async create(payload: DepartmentCreate): Promise<Department> {
    const { data } = await apiClient.post<Department>("/departments", payload);
    return data;
  },
  async update(id: string, payload: Partial<DepartmentCreate>): Promise<Department> {
    const { data } = await apiClient.patch<Department>(`/departments/${id}`, payload);
    return data;
  },
  async remove(id: string): Promise<void> {
    await apiClient.delete(`/departments/${id}`);
  },
};

export const rolesApi = {
  async list(): Promise<Role[]> {
    const { data } = await apiClient.get<Role[]>("/roles");
    return data;
  },
  async myPermissions(): Promise<string[]> {
    const { data } = await apiClient.get<string[]>("/roles/me");
    return data;
  },
  async knownPermissions(): Promise<string[]> {
    const { data } = await apiClient.get<string[]>("/roles/permissions");
    return data;
  },
};

export const usersApi = {
  async me(): Promise<User> {
    const { data } = await apiClient.get<User>("/users/me");
    return data;
  },
  async list(): Promise<User[]> {
    const { data } = await apiClient.get<User[]>("/users");
    return data;
  },
};

export const onboardingApi = {
  async complete(payload: OnboardingState): Promise<{ status: string }> {
    const { data } = await apiClient.post<{ status: string }>("/onboarding/complete", payload);
    return data;
  },
};
