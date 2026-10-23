// TypeScript interfaces and types for the AI Task Manager application

/**
 * Task status enum
 */
export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
}

/**
 * Task priority enum
 */
export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
}

/**
 * Core Task interface
 */
export interface Task {
  id: number;
  title: string;
  description?: string;
  deadline: string; // ISO 8601 datetime string
  completed: boolean;
  status: TaskStatus;
  priority?: TaskPriority;
  summary?: string;
  ai_insult?: string; // Funny AI-generated insult for overdue tasks
  created_at: string;
  updated_at: string;
  is_overdue?: boolean;
}

/**
 * Task creation payload
 */
export interface TaskCreate {
  title: string;
  description?: string;
  deadline: string;
  priority?: TaskPriority;
}

/**
 * Task update payload
 */
export interface TaskUpdate {
  title?: string;
  description?: string;
  deadline?: string;
  completed?: boolean;
  status?: TaskStatus;
  priority?: TaskPriority;
  summary?: string;
}

/**
 * Summary generation response
 */
export interface SummaryResponse {
  task_id: number;
  summary: string;
  generated_at: string;
}

/**
 * AI Edit request
 */
export interface AIEditRequest {
  task_id: number;
  prompt: string;
}

/**
 * AI Insult response
 */
export interface InsultResponse {
  task_id: number;
  insult: string;
  generated_at: string;
}

/**
 * Analytics data structure
 */
export interface Analytics {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completion_rate: number; // Percentage
  on_time_completion_rate: number; // Percentage
  average_delay_hours?: number;
  productivity_trend: ProductivityDataPoint[];
  completion_timeline: CompletionDataPoint[];
  deadline_adherence: DeadlineAdherence;
  recent_activity: RecentActivity[];
}

/**
 * Productivity trend data point
 */
export interface ProductivityDataPoint {
  date: string;
  completed: number;
  created: number;
}

/**
 * Completion timeline data point
 */
export interface CompletionDataPoint {
  date: string;
  completed: number;
}

/**
 * Deadline adherence breakdown
 */
export interface DeadlineAdherence {
  on_time: number;
  late: number;
  pending: number;
}

/**
 * Recent activity item
 */
export interface RecentActivity {
  id: number;
  task_id: number;
  task_title: string;
  action: 'created' | 'completed' | 'updated' | 'overdue';
  timestamp: string;
  details?: string;
}

/**
 * API Error response
 */
export interface APIError {
  detail: string;
  status?: number;
}

/**
 * Task filter options
 */
export interface TaskFilters {
  completed?: boolean;
  overdue?: boolean;
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

/**
 * Loading state for async operations
 */
export interface LoadingState {
  isLoading: boolean;
  error?: string | null;
}

/**
 * Toast notification type
 */
export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}
