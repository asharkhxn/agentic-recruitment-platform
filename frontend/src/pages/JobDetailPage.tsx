import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, FileText, PoundSterling } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import { useJob } from "@/hooks/useJobs";
import { useCreateApplication } from "@/hooks/useApplications";
import { formatDate } from "@/utils/helpers";
import { useAuth } from "@/hooks/useAuth";

export const JobDetailPage = () => {
  const { jobId } = useParams();
  const { data: job, isLoading, isError } = useJob(jobId ?? "");
  const createApplication = useCreateApplication();
  const { user } = useAuth();

  const [coverLetter, setCoverLetter] = useState("");
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [motivation, setMotivation] = useState("");
  const [proudProject, setProudProject] = useState("");
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);

  const applicantName = useMemo(() => {
    if (!user) return "";
    return user.full_name || user.email;
  }, [user]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!jobId) {
      setFeedback({
        type: "error",
        message: "Missing job identifier. Please return to job listings.",
      });
      return;
    }

    if (!cvFile) {
      setFeedback({
        type: "error",
        message: "Please attach your CV before submitting.",
      });
      return;
    }

    try {
      setFeedback(null);
      const formData = new FormData();
      formData.append("job_id", jobId);
      formData.append("cv_file", cvFile);
      formData.append("motivation", motivation.trim());
      formData.append("proud_project", proudProject.trim());
      if (coverLetter.trim().length > 0) {
        formData.append("cover_letter", coverLetter.trim());
      }

      await createApplication.mutateAsync(formData);
      setFeedback({
        type: "success",
        message:
          "Application submitted successfully. We will be in touch soon.",
      });
      setCoverLetter("");
      setCvFile(null);
      setMotivation("");
      setProudProject("");
      setFileInputKey((key) => key + 1);
    } catch (error: unknown) {
      const message =
        error instanceof Error
          ? error.message
          : "We could not submit your application. Please try again.";
      setFeedback({ type: "error", message });
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError || !job) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-24">
        <div className="mb-10 flex items-center gap-2 text-sm text-white/70">
          <ArrowLeft className="h-4 w-4" />
          <Link to="/jobs" className="text-primary hover:underline">
            Back to job listings
          </Link>
        </div>
        <ErrorMessage message="We couldn't load this job. Please return to the listings and try again." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-16 text-white">
      <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-2 text-sm text-white/70 transition hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to job listings
        </Link>
        <span className="text-xs uppercase tracking-[0.3em] text-white/40">
          Posted {formatDate(job.created_at)}
        </span>
      </div>

      <div className="grid gap-8 lg:grid-cols-[2fr,1fr]">
        <Card className="relative overflow-hidden">
          <div className="pointer-events-none absolute -right-40 top-0 h-64 w-64 rounded-full bg-gradient-to-br from-[#6a6dff]/40 to-[#f3a9ff]/30 blur-3xl" />
          <CardHeader className="relative space-y-4">
            <span className="accent-pill">Open role</span>
            <CardTitle className="text-3xl font-semibold leading-tight sm:text-4xl">
              {job.title}
            </CardTitle>
            {job.salary && (
              <div className="flex items-center gap-2 text-sm font-medium text-white/70">
                <PoundSterling className="h-4 w-4 text-white/60" />
                <span>{job.salary}</span>
              </div>
            )}
          </CardHeader>
          <CardContent className="relative space-y-8 text-white/75">
            <section className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-white/50">
                Role overview
              </h3>
              <p className="text-sm leading-relaxed text-white/75 whitespace-pre-line">
                {job.description}
              </p>
            </section>

            {job.requirements && (
              <section className="space-y-3">
                <h3 className="text-sm font-semibold uppercase tracking-[0.25em] text-white/50">
                  Requirements
                </h3>
                <p className="text-sm leading-relaxed text-white/75 whitespace-pre-line">
                  {job.requirements}
                </p>
              </section>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-white/5 backdrop-blur">
          <CardHeader className="space-y-3">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-white/50">
              <FileText className="h-4 w-4" />
              Submit your application
            </div>
            <CardTitle className="text-xl text-white">
              Share your details
            </CardTitle>
            <p className="text-sm text-white/60">
              Attach your CV and optionally include a short cover letter to
              highlight your experience.
            </p>
          </CardHeader>
          <CardContent>
            {feedback?.type === "success" && (
              <div className="mb-4 rounded-2xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100">
                {feedback.message}
              </div>
            )}
            {feedback?.type === "error" && (
              <div className="mb-4 rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {feedback.message}
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="applicantName">Full name</Label>
                <Input
                  id="applicantName"
                  name="applicantName"
                  value={applicantName}
                  readOnly
                  disabled
                  className="cursor-not-allowed opacity-80"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cv">CV (PDF or DOCX)</Label>
                <Input
                  key={fileInputKey}
                  id="cv"
                  name="cv"
                  type="file"
                  accept=".pdf,.doc,.docx"
                  required
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    setCvFile(file);
                  }}
                  className="rounded-2xl border-dashed border-white/20 bg-white/10 file:mr-4 file:rounded-full file:border-0 file:bg-white/20 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white/90 hover:file:bg-white/30"
                />
                {cvFile && (
                  <p className="text-xs text-white/50">
                    Selected file: {cvFile.name}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="motivation">Why do you want to join?</Label>
                <Textarea
                  id="motivation"
                  name="motivation"
                  value={motivation}
                  onChange={(event) => setMotivation(event.target.value)}
                  placeholder="Tell us what excites you about this company and role."
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="proudProject">
                  Tell us about work you are most proud of
                </Label>
                <Textarea
                  id="proudProject"
                  name="proudProject"
                  value={proudProject}
                  onChange={(event) => setProudProject(event.target.value)}
                  placeholder="Share an achievement or project that showcases your strengths."
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="coverLetter">Cover letter (optional)</Label>
                <Textarea
                  id="coverLetter"
                  name="coverLetter"
                  value={coverLetter}
                  onChange={(event) => setCoverLetter(event.target.value)}
                  placeholder="Share a short note about why you're a great fit for this role."
                  className="min-h-[160px]"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={createApplication.isPending}
              >
                {createApplication.isPending
                  ? "Submitting…"
                  : "Submit application"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
