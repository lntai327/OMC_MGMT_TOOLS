import React from 'react';
import { Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { JobStatusResponse } from '../../../models/job.types';

interface JobProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  job: JobStatusResponse | null;
}

export const JobProgressModal: React.FC<JobProgressModalProps> = ({
  isOpen,
  onClose,
  title,
  job,
}) => {
  if (!job) return null;

  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';
  const isRunning = job.status === 'pending' || job.status === 'processing';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="md">
      <div className="py-2 text-center">
        {/* Status Icon */}
        <div className="flex justify-center mb-4">
          {isRunning && (
            <div className="w-14 h-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center animate-pulse">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          )}
          {isCompleted && (
            <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle className="w-8 h-8" />
            </div>
          )}
          {isFailed && (
            <div className="w-14 h-14 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertCircle className="w-8 h-8" />
            </div>
          )}
        </div>

        {/* Status Text */}
        <h4 className="text-xl font-black text-slate-900 mb-1">
          {job.status === 'pending' && 'Đang xử lý...'}
          {job.status === 'processing' && 'Đang xử lý.....'}
          {job.status === 'completed' && 'Hoàn thành!'}
          {job.status === 'failed' && 'Thất bại!'}
        </h4>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 rounded-full h-5 mb-2 overflow-hidden border-2 border-slate-200 shadow-inner">
          <div
            className={`h-full transition-all duration-300 rounded-full ${isCompleted
              ? 'bg-emerald-500'
              : isFailed
                ? 'bg-rose-500'
                : 'bg-brand-600'
              }`}
            style={{ width: `${Math.min(100, Math.max(5, job.progress))}%` }}
          />
        </div>
        <div className="flex justify-between text-sm font-bold text-slate-700 mb-6">
          <span>Tiến độ xử lý</span>
          <span className="text-brand-700">{job.progress}%</span>
        </div>

        {/* Result Metadata / Error info */}
        {job.result_meta && (
          <div className="bg-slate-50 rounded-xl p-4 text-left text-sm mb-6 border-2 border-slate-200 space-y-1.5">
            <h5 className="font-bold text-slate-900 text-base mb-2">
              Chi tiết kết quả:
            </h5>

            {job.result_meta.failed_counter !== undefined && (
              <div className="flex justify-between py-1">
                <span className="font-medium text-slate-900 text-base whitespace-pre-wrap">Lỗi:</span>

                <span
                  className={`font-medium text-base ${job.result_meta.failed_counter > 0
                    ? "text-rose-900"
                    : "text-green-900"
                    }`}
                >
                  {job.result_meta.failed_counter}
                </span>
              </div>
            )}

            {job.result_meta.detail !== undefined && (
              <div className="font-medium text-slate-900 text-base whitespace-pre-wrap">
                {job.result_meta.detail}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-center gap-3 pt-2">
          {isCompleted && job.download_url && (() => {
            // When download_url is relative (e.g. /api/v1/downloads/...), use it directly
            // so browser automatically resolves against the current host/port/protocol (IP, domain, localhost).
            // Only prepend host if VITE_API_BASE_URL is explicitly set to an absolute URL.
            let href = job.download_url;
            if (!href.startsWith('http://') && !href.startsWith('https://')) {
              const envBase = import.meta.env.VITE_API_BASE_URL;
              if (envBase && (envBase.startsWith('http://') || envBase.startsWith('https://'))) {
                const origin = envBase.replace(/\/api\/v1\/?$/, '');
                href = `${origin}${href.startsWith('/') ? '' : '/'}${href}`;
              }
            }

            // Append JWT token so browser direct download is authorized
            const token = localStorage.getItem('omc_access_token');
            if (token && href) {
              const sep = href.includes('?') ? '&' : '?';
              href = `${href}${sep}token=${encodeURIComponent(token)}`;
            }

            return (
              <a
                href={href}
                download
                className="inline-flex items-center justify-center px-6 py-3 bg-emerald-600 text-white rounded-xl text-base font-bold hover:bg-emerald-700 shadow-md transition-colors"
              >
                <Download className="w-5 h-5 mr-2" />
                Tải kết quả
              </a>
            );
          })()}
          <Button
            variant={isCompleted ? 'outline' : 'secondary'}
            size="md"
            onClick={onClose}
            className="font-bold px-6"
          >
            {isRunning ? 'Ẩn tiến trình' : 'Đóng'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

