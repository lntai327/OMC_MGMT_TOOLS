import { apiClient } from './api.client';
import { JobStatusResponse } from '../models/job.types';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1/ws';

export const jobService = {
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await apiClient.get<JobStatusResponse>(`/jobs/${jobId}`);
    return response.data;
  },

  trackJob(
    jobId: string,
    onProgress: (status: JobStatusResponse) => void,
    onComplete: (status: JobStatusResponse) => void,
    onError: (error: string) => void
  ): () => void {
    let ws: WebSocket | null = null;
    let pollInterval: any = null;
    let isTerminated = false;

    // Helper to finish tracking
    const cleanup = () => {
      isTerminated = true;
      if (ws) {
        ws.close();
        ws = null;
      }
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    // Helper to evaluate job state
    const handleStatusUpdate = async (data: JobStatusResponse) => {
      if (isTerminated) return;
      onProgress(data);

      if (data.status === 'completed') {
        cleanup();
        // Re-fetch from REST API to get download_url (WebSocket event lacks it)
        try {
          const fullStatus = await jobService.getJobStatus(jobId);
          onComplete(fullStatus);
        } catch {
          onComplete(data); // fallback to WS data
        }
      } else if (data.status === 'failed') {
        cleanup();
        // Re-fetch to get full error details
        try {
          const fullStatus = await jobService.getJobStatus(jobId);
          onError(fullStatus.error_message || 'Task failed execution.');
        } catch {
          onError(data.error_message || 'Task failed execution.');
        }
      }
    };

    // 1. Polling fallback every 2 seconds to guarantee progress and completion
    const startPolling = () => {
      if (pollInterval || isTerminated) return;
      pollInterval = setInterval(async () => {
        if (isTerminated) return;
        try {
          const status = await jobService.getJobStatus(jobId);
          await handleStatusUpdate(status);
        } catch (e: any) {
          console.warn('Polling error:', e);
        }
      }, 2000);
    };

    // Luôn khởi động polling định kỳ để không bao giờ bị treo nếu WebSocket miss sự kiện
    startPolling();

    // 2. Try WebSocket for real-time instant push
    try {
      ws = new WebSocket(`${WS_BASE_URL}/jobs/${jobId}`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleStatusUpdate(data);
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      ws.onerror = (err) => {
        console.warn('WebSocket connection error, using polling fallback:', err);
      };

      ws.onclose = () => {
        // ws closed, polling continues until isTerminated
      };
    } catch (e) {
      console.warn('WebSocket initialization failed, using polling:', e);
    }

    // Initial check right away
    jobService.getJobStatus(jobId).then(handleStatusUpdate).catch(() => {});

    return cleanup;
  },
};

