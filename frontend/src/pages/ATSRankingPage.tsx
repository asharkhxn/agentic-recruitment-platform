import { useState, useEffect } from "react";
import { atsApi } from "@/api/ats";
import { filesApi } from "@/api/files";
import { useJobs } from "@/hooks/useJobs";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { RankedApplicant } from "@/types";
import { Trophy, Mail, FileText, X, Download } from "lucide-react";
import { AxiosError } from "axios";

export const ATSRankingPage = () => {
  const { data: jobs } = useJobs();
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [rankedApplicants, setRankedApplicants] = useState<RankedApplicant[]>(
    []
  );
  const [jobTitle, setJobTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewApplicant, setPreviewApplicant] =
    useState<RankedApplicant | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");

  useEffect(() => {
    document.title = "ATS Ranking - Recruitment System";
  }, []);

  const handleRank = async () => {
    if (!selectedJobId) return;

    setLoading(true);
    setError("");

    try {
      const response = await atsApi.rankApplicants(selectedJobId);
      setRankedApplicants(response.applicants);
      setJobTitle(response.job_title);
    } catch (errorResponse) {
      const axiosError = errorResponse as AxiosError<{ detail?: string }>;
      const detail = axiosError.response?.data?.detail;
      const status = axiosError.response?.status;

      let friendlyMessage = detail;
      if (!friendlyMessage) {
        if (status === 404) {
          friendlyMessage =
            "We couldn’t find any applicants tied to this role yet. Invite candidates to apply and try again.";
        } else if (status && status >= 500) {
          friendlyMessage =
            "Our ranking engine is calibrating right now. Give it a moment and try again.";
        } else {
          friendlyMessage =
            "We couldn’t rank applicants just yet. Please try again in a moment.";
        }
      }

      setError(friendlyMessage);
      setRankedApplicants([]);
    } finally {
      setLoading(false);
    }
  };

  const closePreview = () => {
    setPreviewApplicant(null);
    setPreviewUrl("");
    setPreviewLoading(false);
    setPreviewError("");
  };

  const handlePreview = async (applicant: RankedApplicant) => {
    setPreviewApplicant(applicant);
    setPreviewLoading(true);
    setPreviewError("");
    setPreviewUrl("");

    try {
      const { signed_url } = await filesApi.getCvPreview(
        applicant.application_id
      );
      setPreviewUrl(signed_url);
    } catch (previewErr) {
      const axiosError = previewErr as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ||
        "We couldn’t load this CV preview. Try downloading instead.";
      setPreviewError(message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const previewFileExtension = (() => {
    const sourceUrl = previewUrl || previewApplicant?.cv_url;
    if (!sourceUrl) return "";

    const cleanUrl = sourceUrl.split("?")[0];
    const extension = cleanUrl.split(".").pop();

    return extension ? extension.toLowerCase() : "";
  })();
  const supportsInlinePreview = previewFileExtension === "pdf";

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-24">
      <div className="max-w-3xl space-y-5">
        <span className="accent-pill">ATS ranking</span>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">
          Sequence applicants with AI-curated clarity.
        </h1>
        <p className="text-base text-white/70">
          Select any role, and let the engine surface fit scores, explain the
          rationale, and chart the next best move for your talent orbit.
        </p>
      </div>

      <Card>
        <CardHeader className="gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-white">Choose a role to rank</CardTitle>
          <p className="text-xs uppercase tracking-[0.45em] text-white/45">
            powered by RecruitAI
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4 sm:flex-row">
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="flex-1 rounded-2xl border border-white/12 bg-white/[0.06] px-5 py-3 text-sm text-white shadow-[0_18px_45px_rgba(9,10,28,0.35)] focus:border-white/25 focus:outline-none focus:ring-2 focus:ring-white/15"
            >
              <option value="" className="bg-[#0e0f24] text-white">
                Select a job…
              </option>
              {jobs?.map((job) => (
                <option
                  key={job.id}
                  value={job.id}
                  className="bg-[#0e0f24] text-white"
                >
                  {job.title}
                </option>
              ))}
            </select>
            <Button
              onClick={handleRank}
              disabled={!selectedJobId || loading}
              className="sm:w-auto"
            >
              {loading ? "Ranking…" : "Rank applicants"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="space-y-4">
          <ErrorMessage
            title="Ranking temporarily unavailable"
            message={error}
          />
          <div className="flex flex-wrap gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRank}
              disabled={loading || !selectedJobId}
            >
              Try again
            </Button>
            <p className="text-xs text-white/50">
              If this keeps happening, double-check that applicants have been
              submitted for the selected role.
            </p>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      )}

      {!loading && rankedApplicants.length > 0 && (
        <div className="space-y-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-2xl font-semibold text-white">
              Ranked applicants for “{jobTitle}”
            </h2>
            <span className="text-xs uppercase tracking-[0.4em] text-white/45">
              score informed summaries
            </span>
          </div>
          {rankedApplicants.map((applicant, index) => (
            <Card
              key={applicant.applicant_id}
              className="transition-all duration-500 hover:shadow-[0_45px_120px_rgba(9,10,28,0.55)]"
            >
              <CardContent className="flex flex-col gap-6 px-8 py-8 lg:flex-row lg:items-center lg:gap-8">
                <div className="flex h-14 w-14 items-center justify-center self-start rounded-full bg-white/10 text-lg font-semibold text-white shadow-[0_15px_35px_rgba(104,107,255,0.35)]">
                  #{index + 1}
                </div>

                <div className="flex-1 space-y-3">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
                    <h3 className="text-lg font-semibold text-white">
                      {applicant.name}
                    </h3>
                    <span className="flex items-center gap-2 text-sm text-white/60">
                      <Mail className="h-4 w-4" />
                      {applicant.email}
                    </span>
                  </div>
                  <p className="text-sm text-white/70">{applicant.summary}</p>
                  <div className="flex flex-wrap gap-2">
                    {applicant.skills.map((skill, i) => (
                      <span
                        key={i}
                        className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.2em] text-white/70"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex w-full flex-row justify-between gap-4 rounded-2xl border border-white/10 bg-white/5 px-6 py-4 text-sm text-white/70 lg:w-auto lg:flex-col lg:items-end">
                  <div className="flex items-center gap-2 text-primary">
                    <Trophy className="h-5 w-5" />
                    <span className="text-2xl font-semibold text-white">
                      {applicant.score}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handlePreview(applicant)}
                    className="flex items-center gap-2 text-xs uppercase tracking-[0.4em] text-white/70 transition hover:text-white"
                  >
                    <FileText className="h-4 w-4" />
                    View CV
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!loading && rankedApplicants.length === 0 && selectedJobId && !error && (
        <p className="rounded-3xl border border-white/10 bg-white/5 py-12 text-center text-sm text-white/60">
          No applicants surfaced for this role yet.
        </p>
      )}

      {previewApplicant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="relative flex h-[80vh] w-[92vw] max-w-4xl flex-col overflow-hidden rounded-3xl border border-white/15 bg-[#101226] shadow-[0_55px_160px_rgba(9,10,28,0.75)]">
            <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
              <div>
                <h3 className="text-lg font-semibold text-white">
                  {previewApplicant.name}
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
                supportsInlinePreview && (
                  <iframe
                    title={`CV preview for ${previewApplicant.name}`}
                    src={`${previewUrl}#toolbar=0`}
                    className="h-full w-full rounded-2xl border border-white/10 bg-white"
                  />
                )}

              {!previewLoading &&
                !previewError &&
                previewUrl &&
                !supportsInlinePreview && (
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
                )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
