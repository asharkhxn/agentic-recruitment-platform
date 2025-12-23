import { useJobs } from "@/hooks/useJobs";
import { JobCard } from "@/components/JobCard";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Search } from "lucide-react";
import { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/Card";

export const JobListingsPage = () => {
  const { data: jobs, isLoading, error, refetch, isFetching } = useJobs();
  const [searchTerm, setSearchTerm] = useState("");
  const quickPicks = ["AI engineer", "Remote-first", "Leadership", "Contract"];

  useEffect(() => {
    document.title = "Talent Orbit";
  }, []);

  const filteredJobs = jobs?.filter(
    (job) =>
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.description.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const resultsCount = filteredJobs?.length ?? 0;
  const hasActiveSearch = searchTerm.trim().length > 0;

  const handleQuickPick = (term: string) => {
    setSearchTerm(term);
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
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-20">
        <ErrorMessage
          title="We can’t reach the roles right now"
          message="A quick refresh usually does the trick. If it keeps happening, our team’s already on it."
        />
        <Button
          onClick={() => refetch()}
          disabled={isFetching}
          className="w-max"
        >
          {isFetching ? "Reconnecting…" : "Try again"}
        </Button>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-24 mx-auto h-[420px] w-[420px] rounded-full bg-gradient-to-br from-[#6a6dff]/25 via-[#9f7bff]/35 to-[#f8b7ff]/15 blur-3xl" />

      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 pt-24 pb-12 lg:pt-32">
        <span className="accent-pill">RecruitAI Studio</span>
        <div className="max-w-3xl space-y-6">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            Navigate the talent universe with effortless clarity.
          </h1>
          <p className="text-base text-white/70 sm:text-lg">
            Discover open roles curated by AI, understand requirements
            instantly, and move candidates forward with confidence. Every
            listing is wrapped in clarity so your next hire feels inevitable.
          </p>
        </div>

        <Card className="border-white/10 bg-white/5">
          <CardContent className="flex flex-col gap-6 px-6 py-6 sm:px-8 sm:py-8">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="relative w-full sm:max-w-xl">
                <Search className="absolute left-6 top-1/2 h-5 w-5 -translate-y-1/2 text-white/40" />
                <Input
                  placeholder="Search roles, stacks, or domains"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="rounded-full border-white/15 bg-[#0e0f24]/80 pl-14 pr-14"
                />
                {hasActiveSearch && (
                  <button
                    type="button"
                    onClick={() => setSearchTerm("")}
                    className="absolute right-6 top-1/2 -translate-y-1/2 text-sm text-white/60 transition hover:text-white"
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="flex gap-3">
                <Link to="/chatbot">
                  <Button variant="ghost" size="sm" className="px-5">
                    Ask the AI assistant
                  </Button>
                </Link>
                <Link to="/signup">
                  <Button size="sm" className="px-5">
                    Join the platform
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-sm text-white/60">
              <span className="uppercase tracking-[0.35em] text-xs text-white/40">
                Quick picks
              </span>
              {quickPicks.map((term) => (
                <Button
                  key={term}
                  size="sm"
                  variant={searchTerm === term ? "secondary" : "ghost"}
                  className="rounded-full border border-white/15 px-4"
                  onClick={() => handleQuickPick(term)}
                >
                  {term}
                </Button>
              ))}
            </div>

            <div className="flex flex-col gap-2 text-sm text-white/60 sm:flex-row sm:items-center sm:justify-between">
              <p>
                {resultsCount === 0
                  ? "No active roles match this filter just yet."
                  : `Showing ${resultsCount} role${
                      resultsCount === 1 ? "" : "s"
                    } tuned to your filters.`}
              </p>
              <p className="text-xs uppercase tracking-[0.35em] text-white/40">
                {hasActiveSearch
                  ? "refined by your search"
                  : "showing all openings"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 pb-24">
        {filteredJobs && filteredJobs.length > 0 ? (
          <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3">
            {filteredJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        ) : (
          <div className="mx-auto max-w-xl rounded-3xl border border-white/10 bg-white/5 px-8 py-10 text-center">
            <span className="accent-pill mb-4 inline-flex">No matches yet</span>
            <h3 className="text-2xl font-semibold text-white">
              We’ll surface new roles soon
            </h3>
            <p className="mt-3 text-sm text-white/65">
              None of the current postings align with that search. Save the
              filters you care about and check back—fresh roles drop often.
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-6"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              {isFetching ? "Refreshing…" : "Refresh roles"}
            </Button>
          </div>
        )}
      </section>
    </div>
  );
};
