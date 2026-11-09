export type JobType = 'import' | 'export';
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface JobCreateResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  download_url?: string | null;
  result_meta?: {
    failed_counter?: number;
    detail?: string;
    filename?: string;
    [key: string]: any;
  } | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

