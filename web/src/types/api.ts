/**
 * SelfDiary Web — API response types and shared interfaces.
 *
 * These types mirror the backend API envelope.
 * Keep in sync with backend Pydantic schemas.
 */

/** Standard API response envelope */
export interface ApiResponse<T> {
  data: T;
  meta: ApiMeta | null;
  error: ApiError | null;
}

export interface ApiMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface ApiError {
  code: string;
  message: string;
}

/** Mood enum — matches backend CHECK constraint */
export type Mood = 'great' | 'good' | 'neutral' | 'bad' | 'terrible';

/** User profile */
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
}

/** Auth tokens returned from login */
export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/** Diary entry */
export interface Entry {
  id: string;
  title: string | null;
  body: string;
  mood: Mood | null;
  is_favorite: boolean;
  version: number;
  tags: Tag[];
  attachment_count: number;
  created_at: string;
  updated_at: string;
}

/** Tag */
export interface Tag {
  id: string;
  name: string;
  color: string | null;
  entry_count?: number;
  created_at: string;
}
