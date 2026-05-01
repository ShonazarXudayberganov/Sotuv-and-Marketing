export type Industry =
  | "savdo"
  | "restoran"
  | "salon-klinika"
  | "talim"
  | "xizmat"
  | "it"
  | "boshqa";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
}

export interface Tenant {
  id: string;
  name: string;
  schema_name: string;
  industry: string | null;
}

export interface AuthBundle {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  tenant: Tenant;
}

export interface RegisterPayload {
  company_name: string;
  industry: Industry;
  phone: string;
  email: string;
  password: string;
  accept_terms: boolean;
}

export interface RegisterResponse {
  verification_id: string;
  phone_masked: string;
  expires_in_seconds: number;
}

export interface VerifyPhonePayload {
  verification_id: string;
  code: string;
}

export interface LoginPayload {
  email_or_phone: string;
  password: string;
  remember_me?: boolean;
}

export interface ApiError {
  detail: string | { msg: string; loc?: string[] }[];
}

export interface Department {
  id: string;
  name: string;
  parent_id: string | null;
  head_user_id: string | null;
  description: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface DepartmentCreate {
  name: string;
  parent_id?: string | null;
  description?: string | null;
  sort_order?: number;
}

export interface Role {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  is_system: boolean;
  permissions: string[];
}

export interface OnboardingState {
  step: number;
  completed: boolean;
  company?: Record<string, unknown>;
  departments?: string[];
  invited_users?: string[];
  selected_modules?: string[];
  selected_plan?: string | null;
}

export const MODULES = [
  { key: "crm", label: "CRM", price: { start: 290_000, pro: 690_000, business: 1_400_000 } },
  { key: "smm", label: "SMM", price: { start: 390_000, pro: 890_000, business: 1_800_000 } },
  {
    key: "ads",
    label: "Reklama",
    price: { start: 290_000, pro: 690_000, business: 1_400_000 },
  },
  {
    key: "inbox",
    label: "Inbox",
    price: { start: 390_000, pro: 890_000, business: 1_800_000 },
  },
  {
    key: "reports",
    label: "Hisobotlar",
    price: { start: 190_000, pro: 490_000, business: 990_000 },
  },
  {
    key: "integrations",
    label: "Integratsiyalar",
    price: { start: 190_000, pro: 490_000, business: 990_000 },
  },
] as const;

export type ModuleKey = (typeof MODULES)[number]["key"];

export const PLANS = [
  { key: "start", label: "Start", priceTotal: 690_000 },
  { key: "pro", label: "Pro", priceTotal: 1_500_000, recommended: true },
  { key: "business", label: "Business", priceTotal: 3_000_000 },
] as const;

export type TaskStatus = "new" | "in_progress" | "review" | "done" | "cancelled";
export type TaskPriority = "low" | "medium" | "high" | "critical";

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  department_id: string | null;
  related_type: string | null;
  related_id: string | null;
  starts_at: string | null;
  due_at: string | null;
  estimated_hours: number | null;
  created_by: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: string | null;
  department_id?: string | null;
  starts_at?: string | null;
  due_at?: string | null;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  rate_limit_per_minute: number;
  expires_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface ApiKeyCreated extends ApiKey {
  plaintext_key: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  body: string | null;
  category: string;
  severity: string;
  read_at: string | null;
  created_at: string;
}

export interface TwoFactorSetup {
  secret: string;
  qr_data_url: string;
  backup_codes: string[];
}

export interface Subscription {
  id: string;
  selected_modules: string[];
  tier: string;
  package: string | null;
  billing_cycle_months: number;
  price_total: number;
  discount_percent: number;
  starts_at: string;
  expires_at: string;
  is_trial: boolean;
  is_active: boolean;
  cancelled_at: string | null;
}

export type GraceState = "active" | "banner" | "read_only" | "locked";

export interface BillingStatus {
  subscription: Subscription | null;
  grace_state: GraceState;
  days_until_expiry: number | null;
  days_past_expiry: number | null;
}

export interface InvoiceRow {
  id: string;
  subscription_id: string;
  invoice_number: string;
  amount: number;
  status: string;
  payment_method: string;
  paid_at: string | null;
  due_at: string;
  notes: string | null;
  created_at: string;
}

export interface PriceQuote {
  price_total: number;
  discount_percent: number;
  ai_token_cap_monthly: number;
}

export interface BillingCatalog {
  modules: { key: string; label: string; prices: Record<string, number> }[];
  packages: Record<string, { modules: string[]; discount_percent: number; label: string }>;
  cycle_discounts: Record<string, number>;
  ai_token_caps: Record<string, number>;
}

// ─────────── SMM / Sprint 1.1 ───────────

export interface Brand {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  industry: string | null;
  logo_url: string | null;
  primary_color: string | null;
  voice_tone: string | null;
  target_audience: string | null;
  languages: string[];
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BrandCreate {
  name: string;
  description?: string | null;
  industry?: string | null;
  logo_url?: string | null;
  primary_color?: string | null;
  voice_tone?: string | null;
  target_audience?: string | null;
  languages?: string[];
  is_default?: boolean;
}

export type IntegrationCategory = "ai" | "social" | "auth" | "messaging";

export interface IntegrationProvider {
  provider: string;
  label: string;
  category: IntegrationCategory;
  description: string;
  secret_fields: string[];
  display_field: string | null;
  docs_url: string | null;
  connected: boolean;
  is_active: boolean;
  label_custom: string | null;
  display_value: string | null;
  masked_values: Record<string, string>;
  last_verified_at: string | null;
  last_error: string | null;
  updated_at: string | null;
}

export interface IntegrationConnect {
  label?: string;
  credentials: Record<string, string>;
  metadata?: Record<string, unknown>;
}

// ─────────── Knowledge Base / Sprint 1.2 ───────────

export interface KnowledgeDocument {
  id: string;
  brand_id: string;
  title: string;
  source_type: string;
  source_url: string | null;
  chunk_count: number;
  embed_status: "processing" | "ready" | "empty" | "failed" | string;
  embed_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeStats {
  documents: number;
  chunks: number;
}

export interface KnowledgeSearchHit {
  chunk_id: string;
  document_id: string;
  document_title: string;
  brand_id: string;
  position: number;
  content: string;
  token_count: number;
  similarity: number;
}

export interface KnowledgeSearchResponse {
  query: string;
  hits: KnowledgeSearchHit[];
}

export interface TextDocumentCreate {
  brand_id: string;
  title: string;
  text: string;
  source_url?: string | null;
}

// ─────────── Social accounts / Sprint 1.3 ───────────

export interface SocialAccount {
  id: string;
  brand_id: string;
  provider: string;
  external_id: string;
  external_handle: string | null;
  external_name: string | null;
  chat_type: string | null;
  is_active: boolean;
  last_published_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelegramBotInfo {
  username: string | null;
  first_name: string | null;
  bot_id: number | null;
  can_join_groups: boolean | null;
  mocked: boolean;
}

export interface TelegramSendResult {
  message_id: number;
  chat_id: number | string;
  sent_text: string;
  mocked: boolean;
}

export interface MetaPageOption {
  id: string;
  name: string;
  category: string | null;
  has_instagram: boolean;
  instagram_username: string | null;
}

export interface MetaSendResult {
  post_id: string;
  sent_text: string;
  target: "facebook" | "instagram";
  mocked: boolean;
}

export interface YouTubeChannelInfo {
  id: string;
  title: string;
  handle: string | null;
  description: string | null;
  thumbnail_url: string | null;
  subscribers: number;
  views: number;
  videos: number;
  mocked: boolean;
}

export interface YouTubeVideo {
  id: string;
  title: string;
  published_at: string | null;
  view_count: number;
  like_count: number;
  comment_count: number;
  thumbnail_url: string | null;
}

export interface YouTubeStats {
  account_id: string;
  subscribers: number;
  views: number;
  videos: number;
  recent: YouTubeVideo[];
  mocked: boolean;
}

// ─────────── AI content / Sprint 1.6 ───────────

export type ContentPlatform =
  | "telegram"
  | "instagram"
  | "facebook"
  | "youtube"
  | "generic";

export interface ContentDraft {
  id: string;
  brand_id: string;
  platform: ContentPlatform | string;
  title: string | null;
  body: string;
  user_goal: string | null;
  language: string;
  provider: string | null;
  model: string | null;
  tokens_used: number;
  rag_chunk_ids: string[] | null;
  is_starred: boolean;
  created_at: string;
  updated_at: string;
}

export interface GeneratePostRequest {
  brand_id: string;
  platform: ContentPlatform | string;
  user_goal: string;
  language?: string;
  title?: string | null;
  use_cache?: boolean;
}

export interface AIUsage {
  period: string;
  tokens_used: number;
  tokens_cap: number;
}

export interface ContentStats {
  drafts_total: number;
  drafts_starred: number;
  by_platform: Record<string, number>;
}

// ─────────── Posts / Sprint 1.7 ───────────

export type PostStatus =
  | "draft"
  | "scheduled"
  | "publishing"
  | "published"
  | "partial"
  | "failed"
  | "cancelled";

export interface PostPublication {
  id: string;
  post_id: string;
  social_account_id: string;
  provider: string;
  status: string;
  attempts: number;
  next_retry_at: string | null;
  external_post_id: string | null;
  last_error: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  brand_id: string;
  draft_id: string | null;
  title: string | null;
  body: string;
  media_urls: string[] | null;
  status: PostStatus | string;
  scheduled_at: string | null;
  published_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface PostDetail extends Post {
  publications: PostPublication[];
}

export interface PostCreateRequest {
  brand_id: string;
  body: string;
  title?: string | null;
  media_urls?: string[] | null;
  social_account_ids: string[];
  scheduled_at?: string | null;
  draft_id?: string | null;
}

export interface PostStats {
  total: number;
  by_status: Record<string, number>;
}

export interface CalendarDay {
  date: string;
  posts: Post[];
}

export interface CalendarResponse {
  start: string;
  end: string;
  days: CalendarDay[];
}

// ─────────── Analytics / Sprint 1.9 ───────────

export interface AnalyticsPlatformBucket {
  posts: number;
  views: number;
  likes: number;
  comments: number;
  shares: number;
}

export interface AnalyticsOverview {
  total_posts: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  engagement_rate: number;
  by_platform: Record<string, AnalyticsPlatformBucket>;
}

export interface AnalyticsTimePoint {
  date: string;
  posts: number;
  views: number;
  likes: number;
  comments: number;
  shares: number;
}

export interface TopPost {
  post_id: string;
  publication_id: string;
  provider: string;
  title: string;
  external_post_id: string | null;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  engagement: number;
  published_at: string | null;
}

export interface OptimalCell {
  weekday: number;
  hour: number;
  posts: number;
  avg_engagement: number;
  views: number;
}

export interface OptimalTimes {
  cells: OptimalCell[];
  best: OptimalCell[];
}

export interface AnalyticsInsights {
  summary: string;
  recommendations: string[];
  snapshot: AnalyticsOverview;
  optimal: OptimalTimes;
  top_posts: TopPost[];
}

// ─────────── CRM / Sprint 2.1 ───────────

export type ContactStatus = "lead" | "active" | "customer" | "lost" | "archived";

export type ContactActivityKind =
  | "call_in"
  | "call_out"
  | "message_in"
  | "message_out"
  | "email"
  | "note"
  | "task"
  | "meeting"
  | "status_change";

export interface Contact {
  id: string;
  full_name: string;
  company_name: string | null;
  phone: string | null;
  email: string | null;
  telegram_username: string | null;
  instagram_username: string | null;
  industry: string | null;
  source: string | null;
  status: ContactStatus | string;
  department_id: string | null;
  assignee_id: string | null;
  ai_score: number;
  ai_score_reason: string | null;
  ai_score_updated_at: string | null;
  notes: string | null;
  custom_fields: Record<string, unknown> | null;
  tags: string[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContactActivity {
  id: string;
  contact_id: string;
  kind: ContactActivityKind | string;
  title: string | null;
  body: string | null;
  direction: string | null;
  channel: string | null;
  duration_seconds: number | null;
  occurred_at: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactStats {
  total: number;
  by_status: Record<string, number>;
  hot_leads: number;
  new_last_week: number;
}

export interface ContactCreateRequest {
  full_name: string;
  company_name?: string | null;
  phone?: string | null;
  email?: string | null;
  telegram_username?: string | null;
  instagram_username?: string | null;
  industry?: string | null;
  source?: string | null;
  status?: ContactStatus | string;
  department_id?: string | null;
  assignee_id?: string | null;
  notes?: string | null;
  tags?: string[] | null;
}

export interface ActivityCreateRequest {
  kind: ContactActivityKind | string;
  title?: string | null;
  body?: string | null;
  direction?: string | null;
  channel?: string | null;
  duration_seconds?: number | null;
  occurred_at?: string | null;
}
