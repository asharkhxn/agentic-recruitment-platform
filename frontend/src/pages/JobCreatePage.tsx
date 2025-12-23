import { FormEvent, useState } from "react";
import { useCreateJob } from "@/hooks/useJobs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Button } from "@/components/ui/Button";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

export const JobCreatePage = () => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [salary, setSalary] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const createJob = useCreateJob();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSuccess(false);

    try {
      await createJob.mutateAsync({
        title,
        description,
        requirements,
        salary: salary || undefined,
      });

      setTitle("");
      setDescription("");
      setRequirements("");
      setSalary("");
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Failed to create job");
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-16">
      <Card>
        <CardHeader className="space-y-3">
          <span className="accent-pill w-max">Create new role</span>
          <CardTitle className="text-3xl text-white">
            Publish a role to the marketplace
          </CardTitle>
          <p className="text-sm text-white/60">
            Outline the essentials and RecruitAI will surface it to the right
            applicants instantly.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && <ErrorMessage message={error} />}
            {success && (
              <div className="rounded-2xl border border-emerald-400/40 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                Role published successfully. Candidates will start discovering
                it in a few moments.
              </div>
            )}

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-white/70"
                htmlFor="title"
              >
                Role title
              </label>
              <Input
                id="title"
                placeholder="Senior Product Designer"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-white/70"
                htmlFor="description"
              >
                Narrative overview
              </label>
              <Textarea
                id="description"
                placeholder="Share what makes this role unique, who they’ll work with, and the outcomes they’ll drive."
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={5}
                required
              />
            </div>

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-white/70"
                htmlFor="requirements"
              >
                Core requirements
              </label>
              <Textarea
                id="requirements"
                placeholder="List must-have skills, tech stack, and experience level."
                value={requirements}
                onChange={(event) => setRequirements(event.target.value)}
                rows={4}
                required
              />
            </div>

            <div className="space-y-2">
              <label
                className="text-sm font-medium text-white/70"
                htmlFor="salary"
              >
                Salary (optional)
              </label>
              <Input
                id="salary"
                placeholder="£120k – £150k"
                value={salary}
                onChange={(event) => setSalary(event.target.value)}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={createJob.isPending}
            >
              {createJob.isPending ? "Publishing role…" : "Publish role"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
