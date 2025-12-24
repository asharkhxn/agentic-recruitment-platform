import { useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useApplications } from "@/hooks/useApplications";
import { useJobs } from "@/hooks/useJobs";
import { useAuth } from "@/hooks/useAuth";
import { Spinner } from "@/components/ui/Spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { filesApi } from "@/api/files";
import { X, FileText, Download } from "lucide-react";

export const ApplicationsPage = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const jobIdParam = searchParams.get("job_id") ?? undefined;
  const {
    data: applications,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useApplications(jobIdParam);
  const { data: jobs } = useJobs();

  const myApplications = useMemo(() => {
    if (!applications || !user) return [];
    // Applicants see only their own applications. Recruiters see applications returned by the API (filtered by recruiter and optional job_id).
    if (user.role === "applicant") {
      return applications.filter(
        (application) => application.applicant_id === user.id
      );
    }
    return applications;
  }, [applications, user]);

  const jobLookup = useMemo(() => {
    if (!jobs) return new Map<string, { title: string; description: string }>();
    return new Map(
      jobs.map((job) => [
        job.id,
        { title: job.title, description: job.description },
      ])
    );
  }, [jobs]);

  // CV preview state (reuse same behavior as ATSRankingPage)
  const [previewApplication, setPreviewApplication] = useState<any | null>(
    null
  );
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");

  const closePreview = () => {
    setPreviewApplication(null);
    setPreviewUrl("");
    setPreviewLoading(false);
    setPreviewError("");
  };

  const handlePreview = async (application: any) => {
    setPreviewApplication(application);
    setPreviewLoading(true);
    setPreviewError("");
    setPreviewUrl("");

    try {
      const { signed_url } = await filesApi.getCvPreview(application.id);
      setPreviewUrl(signed_url);
    } catch (previewErr: any) {
      const message =
        previewErr?.response?.data?.detail ||
        "We couldn’t load this CV preview. Try downloading instead.";
      setPreviewError(message);
    } finally {
      setPreviewLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-16">
        <ErrorMessage message="We couldn’t load your applications." />
        <Button
          onClick={() => refetch()}
          disabled={isFetching}
          className="w-max"
        >
          {isFetching ? "Retrying…" : "Try again"}
        </Button>
      </div>
    );
  }

  if (!myApplications.length) {
    return (
      <div className="mx-auto w-full max-w-4xl px-6 py-20 text-center text-white/70">
        <span className="accent-pill mb-4 inline-flex">Your applications</span>
        <h2 className="text-3xl font-semibold tracking-tight text-white">
          No submissions just yet
        </h2>
        <p className="mt-3 text-sm sm:text-base">
          Start exploring roles on the Jobs page and submit your first
          application to see it tracked here.
        </p>
        <Button asChild size="sm" className="mt-8">
          <Link to="/jobs">Browse open roles</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-14">
      <div className="mb-10 space-y-3">
        <span className="accent-pill">
          {user?.role === "recruiter" ? "Applicants" : "Your applications"}
        </span>
        <h1 className="text-4xl font-semibold tracking-tight text-white">
          {user?.role === "recruiter"
            ? jobIdParam
              ? `Applicants for ${
                  jobLookup.get(jobIdParam)?.title || "this role"
                }`
              : "Applicants overview"
            : "Progress overview"}
        </h1>
        <p className="text-sm text-white/70">
          {user?.role === "recruiter"
            ? "Review applicants who have applied to your roles. Click any application to view details."
            : "Keep tabs on every opportunity you’ve engaged with. Updates appear instantly as recruiters respond."}
        </p>
      </div>

      <div className="space-y-6">
        {myApplications.map((application) => {
          const job = jobLookup.get(application.job_id);
          return (
            <Card key={application.id} className="border-white/10 bg-white/5">
              <CardHeader>
                <CardTitle className="text-white">
                  {job?.title || "Role no longer available"}
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-4 text-sm text-white/70">
                <p>
                  {job?.description ||
                    "We’re unable to find details for this role."}
                </p>

                {user?.role === "recruiter" ? (
                  <div className="space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-white">
                          {application.applicant_name || "Unknown"}
                        </div>
                        <div className="text-xs text-white/60">
                          {application.applicant_id}
                        </div>
                      </div>

                      <div className="text-right">
                        <button
                          type="button"
                          onClick={() => handlePreview(application)}
                          className="text-sm text-primary hover:underline"
                        >
                          View CV
                        </button>
                        <div className="text-xs text-white/60">
                          Submitted:{" "}
                          {new Date(application.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 text-xs text-white/60">
                      <div>
                        <span className="font-medium text-white/70">
                          Motivation:
                        </span>{" "}
                        {application.motivation || "Not provided"}
                      </div>
                      <div className="mt-2">
                        <span className="font-medium text-white/70">
                          Proudest work:
                        </span>{" "}
                        {application.proud_project || "Not provided"}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4 text-xs text-white/60">
                    <div className="flex flex-col gap-1 sm:flex-row sm:justify-between sm:gap-4">
                      <span className="font-medium text-white/70">
                        Motivation
                      </span>
                      <span className="text-white/60">
                        {application.motivation || "Not provided"}
                      </span>
                    </div>
                    <div className="flex flex-col gap-1 border-t border-white/10 pt-3 sm:flex-row sm:justify-between sm:gap-4">
                      <span className="font-medium text-white/70">
                        Proudest work
                      </span>
                      <span className="text-white/60">
                        {application.proud_project || "Not provided"}
                      </span>
                    </div>
                  </div>
                )}

                {user?.role !== "recruiter" && (
                  <div className="flex flex-col gap-2 text-xs text-white/50 sm:flex-row sm:items-center sm:justify-between">
                    <span>Application ID: {application.id}</span>
                    <span>
                      Submitted:{" "}
                      {new Date(application.created_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      {previewApplication && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="relative flex h-[80vh] w-[92vw] max-w-4xl flex-col overflow-hidden rounded-3xl border border-white/15 bg-[#101226] shadow-[0_55px_160px_rgba(9,10,28,0.75)]">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <div>
                <h3 className="text-lg font-semibold text-white">
                  {previewApplication.applicant_name || "CV preview"}
                </h3>
                <p className="text-xs uppercase tracking-[0.3em] text-white/40">
                  CV preview
                </p>
              </div>
              <button
                type="button"
                onClick={closePreview}
                className="rounded-full border border-white/10 bg-white/5 p-2 text-white/70 transition hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 bg-[#090a1c] p-6">
              {previewLoading && (
                <div className="flex h-full items-center justify-center">
                  <Spinner size="lg" />
                </div>
              )}

              {!previewLoading && previewError && (
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center text-white/70">
                  <FileText className="h-10 w-10 text-white/50" />
                  <p className="max-w-sm text-sm">{previewError}</p>
                  {previewUrl && (
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.4em] text-white/80 hover:text-white"
                    >
                      <Download className="h-4 w-4" />
                      Download CV
                    </a>
                  )}
                </div>
              )}

              {!previewLoading &&
                !previewError &&
                previewUrl &&
                ((
                  previewUrl.split("?")[0].split(".").pop() || ""
                ).toLowerCase() === "pdf" ? (
                  <iframe
                    title={`CV preview`}
                    src={`${previewUrl}#toolbar=0`}
                    className="h-full w-full rounded-2xl border border-white/10 bg-white"
                  />
                ) : (
                  <div className="flex h-full flex-col items-center justify-center gap-4 text-center text-white/70">
                    <FileText className="h-10 w-10 text-white/50" />
                    <p className="max-w-sm text-sm">
                      Inline preview isn’t available for this file type. You can
                      download the CV to view it locally.
                    </p>
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.4em] text-white/80 hover:text-white"
                    >
                      <Download className="h-4 w-4" />
                      Download CV
                    </a>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
