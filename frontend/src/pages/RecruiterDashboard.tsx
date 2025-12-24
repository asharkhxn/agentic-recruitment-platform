import { useEffect, useState } from "react";
import { jobsApi } from "@/api/jobs";
import { applicationsApi } from "@/api/applications";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useNavigate } from "react-router-dom";

interface Job {
  id: string;
  title: string;
  location: string;
  status: string;
  created_at: string;
  application_count: number;
}

export const RecruiterDashboard = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      // Assume recruiter id is stored in localStorage
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        setError("Please login as recruiter.");
        setLoading(false);
        return;
      }
      const user = JSON.parse(userStr);
      const jobsData = await jobsApi.getJobsByRecruiter(user.id);
      // For each job, fetch application count
      const jobsWithCounts = await Promise.all(
        jobsData.map(async (job: any) => {
          const count = await applicationsApi.getApplicationCount(job.id);
          return { ...job, application_count: count };
        })
      );
      setJobs(jobsWithCounts);
    } catch (err: any) {
      setError(err.message || "Failed to fetch jobs.");
    } finally {
      setLoading(false);
    }
  };

  const navigate = useNavigate();
  const navigateToApplications = (jobId: string) => {
    navigate({ pathname: "/applications", search: `?job_id=${jobId}` });
  };

  // Modal state for close confirmation
  const [closingJob, setClosingJob] = useState<Job | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  const openCloseModal = (job: Job) => {
    setClosingJob(job);
  };

  const closeModal = () => {
    setClosingJob(null);
    setModalLoading(false);
  };

  const performCloseJob = async () => {
    if (!closingJob) return;
    try {
      setModalLoading(true);
      await jobsApi.close(closingJob.id);
      closeModal();
      await fetchJobs();
    } catch (err: any) {
      setError(err.message || "Failed to close job.");
      setModalLoading(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-24">
      <h1 className="text-4xl font-semibold mb-8 text-white">
        Recruiter Dashboard
      </h1>
      {loading && <Spinner size="lg" />}
      {error && <div className="text-red-500 mb-4">{error}</div>}
      {jobs.length === 0 && !loading && !error && (
        <div className="text-center text-white/60 text-lg mt-16">
          You haven't posted any jobs yet.
          <br />
          <span className="text-white/40 text-base">
            Click "Create Role" above to add your first job.
          </span>
        </div>
      )}
      {jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <Card
              key={job.id}
              className="bg-white/10 flex flex-col min-h-[300px] overflow-hidden"
            >
              <CardHeader className="flex-1 p-6">
                <CardTitle className="text-white">{job.title}</CardTitle>
                <div className="text-white/70 text-sm mt-1">{job.location}</div>
                <div className="text-white/70 text-xs mt-2">
                  Created: {new Date(job.created_at).toLocaleDateString()}
                </div>
              </CardHeader>
              <CardContent className="flex flex-col justify-between flex-1 p-6">
                <div>
                  <div className="mb-2 text-white/85">
                    Status: {job.status || "Open"}
                  </div>
                  <div className="mb-2 text-white/85">
                    Applications: {job.application_count}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="secondary"
                    className="shrink-0"
                    onClick={() => navigateToApplications(job.id)}
                  >
                    View Applicants
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    className="shrink-0"
                    onClick={() => openCloseModal(job)}
                  >
                    Close Job
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Confirmation modal for closing a job */}
      {closingJob && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-[9998]"
            onClick={closeModal}
          />
          <div className="relative w-full max-w-md rounded-2xl p-6 bg-white/5 border border-white/10 z-[9999]">
            <h3 className="text-lg font-semibold text-white">Close job</h3>
            <p className="mt-2 text-sm text-white/70">
              Are you sure you want to close <strong>{closingJob.title}</strong>
              ? This will prevent new applications.
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <Button variant="ghost" onClick={closeModal} className="px-4">
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={performCloseJob}
                className="px-4"
                disabled={modalLoading}
              >
                {modalLoading ? "Closing…" : "Close job"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecruiterDashboard;
