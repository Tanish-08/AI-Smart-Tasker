// API client for the AI Smart Tasker backend (FastAPI)
import {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskFilters,
  TaskStatus,
  TaskPriority,
  SummaryResponse,
  AIEditRequest,
  InsultResponse,
  Analytics,
} from '@/types/task';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

// The backend needs a user_id on most calls. Change this when you add login.
export const USER_ID = 1;

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    ...options,
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // response had no JSON body
    }
    throw new Error(detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// Convert a backend task into the shape the frontend components expect
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeTask(raw: any): Task {
  const completed = Boolean(raw.completed);
  const deadline: string = raw.deadline;
  const rawPriority = typeof raw.priority === 'string' ? raw.priority.toLowerCase() : undefined;
  const priority = (Object.values(TaskPriority) as string[]).includes(rawPriority ?? '')
    ? (rawPriority as TaskPriority)
    : undefined;

  return {
    ...raw,
    completed,
    status: raw.status ?? (completed ? TaskStatus.COMPLETED : TaskStatus.PENDING),
    priority,
    ai_insult: raw.ai_insult ?? raw.insult_message ?? undefined,
    is_overdue: raw.is_overdue ?? (!completed && new Date(deadline).getTime() < Date.now()),
  } as Task;
}

// ---------- Tasks ----------

export async function getTasks(filters: TaskFilters = {}): Promise<Task[]> {
  const params = new URLSearchParams({ user_id: String(USER_ID) });
  if (filters.completed !== undefined) params.set('completed', String(filters.completed));
  if (filters.overdue) params.set('overdue_only', 'true');

  const data = await request<{ tasks: unknown[] }>(`/tasks?${params.toString()}`);
  let tasks = (data.tasks ?? []).map(normalizeTask);

  if (filters.status) tasks = tasks.filter((t) => t.status === filters.status);
  if (filters.priority) tasks = tasks.filter((t) => t.priority === filters.priority);
  if (filters.search) {
    const q = filters.search.toLowerCase();
    tasks = tasks.filter(
      (t) => t.title.toLowerCase().includes(q) || (t.description ?? '').toLowerCase().includes(q)
    );
  }
  return tasks;
}

export async function getTask(taskId: number): Promise<Task> {
  const raw = await request<unknown>(`/tasks/${taskId}?user_id=${USER_ID}`);
  return normalizeTask(raw);
}

export async function createTask(data: TaskCreate): Promise<Task> {
  const raw = await request<unknown>('/tasks', {
    method: 'POST',
    body: JSON.stringify({ ...data, user_id: USER_ID }),
  });
  return normalizeTask(raw);
}

export async function updateTask(taskId: number, data: TaskUpdate): Promise<Task> {
  const raw = await request<unknown>(`/tasks/${taskId}?user_id=${USER_ID}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  return normalizeTask(raw);
}

export async function deleteTask(taskId: number): Promise<void> {
  await request<void>(`/tasks/${taskId}?user_id=${USER_ID}`, { method: 'DELETE' });
}

// Accepts either a Task object or a task id
export async function toggleTaskCompletion(taskOrId: Task | number, completed?: boolean): Promise<Task> {
  const task = typeof taskOrId === 'number' ? await getTask(taskOrId) : taskOrId;
  const next = completed ?? !task.completed;
  return updateTask(task.id, {
    completed: next,
    status: next ? TaskStatus.COMPLETED : TaskStatus.PENDING,
  });
}

// ---------- Summaries ----------

export async function generateSummary(taskId: number): Promise<SummaryResponse> {
  const data = await request<{ summary: string; generated_at?: string }>('/summaries/generate', {
    method: 'POST',
    body: JSON.stringify({ task_id: taskId, user_id: USER_ID }),
  });
  return { task_id: taskId, summary: data.summary, generated_at: data.generated_at ?? new Date().toISOString() };
}

export async function modifySummary(
  taskIdOrRequest: number | AIEditRequest,
  prompt?: string
): Promise<SummaryResponse> {
  const body =
    typeof taskIdOrRequest === 'number'
      ? { task_id: taskIdOrRequest, prompt: prompt ?? '' }
      : taskIdOrRequest;

  const data = await request<{ summary: string; generated_at?: string }>('/summaries/modify', {
    method: 'POST',
    body: JSON.stringify({ ...body, user_id: USER_ID }),
  });
  return { task_id: body.task_id, summary: data.summary, generated_at: data.generated_at ?? new Date().toISOString() };
}

export async function updateSummaryManually(taskId: number, summary: string): Promise<SummaryResponse> {
  const task = await updateTask(taskId, { summary });
  return { task_id: taskId, summary: task.summary ?? summary, generated_at: new Date().toISOString() };
}

// ---------- Deadlines / insults ----------

export async function regenerateInsult(taskId: number): Promise<InsultResponse> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = await request<any>(`/deadlines/regenerate-insult/${taskId}?user_id=${USER_ID}`, {
    method: 'POST',
  });
  return {
    task_id: taskId,
    insult: data.insult ?? data.insult_message ?? data.ai_insult ?? '',
    generated_at: data.generated_at ?? new Date().toISOString(),
  };
}

// ---------- Analytics ----------

export async function getAnalytics(): Promise<Analytics> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = await request<any>(`/analytics?user_id=${USER_ID}`);
  return {
    total_tasks: 0,
    completed_tasks: 0,
    pending_tasks: 0,
    overdue_tasks: 0,
    completion_rate: 0,
    on_time_completion_rate: 0,
    productivity_trend: [],
    completion_timeline: [],
    deadline_adherence: { on_time: 0, late: 0, pending: 0 },
    recent_activity: [],
    ...data,
  } as Analytics;
}