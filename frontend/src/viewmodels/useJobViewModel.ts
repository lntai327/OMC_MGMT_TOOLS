import { useState, useCallback, useRef } from 'react';
import { JobStatusResponse } from '../models/job.types';
import { jobService } from '../services/job.service';

export function useJobViewModel() {
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [jobTitle, setJobTitle] = useState<string>('');
  const stopTrackingRef = useRef<(() => void) | null>(null);
  // Registry of callbacks to run when a job of a given type completes
  const onCompletedCallbackRef = useRef<(() => void) | null>(null);

  const startTracking = useCallback(
    (jobId: string, title: string = 'Tiến trình xử lý', onCompleted?: () => void) => {
      if (stopTrackingRef.current) {
        stopTrackingRef.current();
      }

      setJobTitle(title);
      setIsModalOpen(true);
      setActiveJob({
        job_id: jobId,
        status: 'pending',
        progress: 0,
      });

      // Store the completion callback for this job
      onCompletedCallbackRef.current = onCompleted ?? null;

      const stopFn = jobService.trackJob(
        jobId,
        (status) => {
          setActiveJob(status);
        },
        (completedStatus) => {
          setActiveJob(completedStatus);
          // Fire the completion callback (e.g. reload table after import)
          if (onCompletedCallbackRef.current) {
            onCompletedCallbackRef.current();
            onCompletedCallbackRef.current = null;
          }
        },
        (errorMsg) => {
          setActiveJob((prev) => ({
            job_id: prev?.job_id || jobId,
            status: 'failed',
            progress: prev?.progress || 0,
            error_message: errorMsg,
          }));
        }
      );

      stopTrackingRef.current = stopFn;
    },
    []
  );

  const closeModal = useCallback(() => {
    if (activeJob?.status === 'processing' || activeJob?.status === 'pending') {
      // Allow closing modal while job continues in background
      setIsModalOpen(false);
    } else {
      setIsModalOpen(false);
      setActiveJob(null);
      if (stopTrackingRef.current) {
        stopTrackingRef.current();
        stopTrackingRef.current = null;
      }
    }
  }, [activeJob]);

  return {
    activeJob,
    isModalOpen,
    jobTitle,
    startTracking,
    closeModal,
  };
}

