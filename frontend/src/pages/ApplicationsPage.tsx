import { useMemo } from "react";
import { useApplications } from "@/hooks/useApplications";
import { useJobs } from "@/hooks/useJobs";
import { useAuth } from "@/hooks/useAuth";
import { Spinner } from "@/components/ui/Spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Link } from "react-router-dom";

export const ApplicationsPage = () => {
  const { user } = useAuth();
  const {
    data: applications,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useApplications();
  const { data: jobs } = useJobs();

  const myApplications = useMemo(() => {
    if (!applications || !user) return [];
    return applications.filter(
      (application) => application.applicant_id === user.id
    );
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
        <span className="accent-pill">Your applications</span>
        <h1 className="text-4xl font-semibold tracking-tight text-white">
          Progress overview
        </h1>
        <p className="text-sm text-white/70">
          Keep tabs on every opportunity you’ve engaged with. Updates appear
          instantly as recruiters respond.
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
                <div className="flex flex-col gap-2 text-xs text-white/50 sm:flex-row sm:items-center sm:justify-between">
                  <span>Application ID: {application.id}</span>
                  <span>
                    Submitted:{" "}
                    {new Date(application.created_at).toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
