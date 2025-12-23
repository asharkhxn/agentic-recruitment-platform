import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/Card";
import { Button } from "./ui/Button";
import { Job } from "@/types";
import { formatDate } from "@/utils/helpers";
import { PoundSterling } from "lucide-react";
import { Link } from "react-router-dom";

interface JobCardProps {
  job: Job;
}

export const JobCard = ({ job }: JobCardProps) => {
  return (
    <Card className="group relative overflow-hidden">
      <div className="pointer-events-none absolute -right-24 top-0 h-48 w-48 rounded-full bg-gradient-to-br from-[#6a6dff]/50 to-[#f3a9ff]/40 blur-3xl opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
      <CardHeader className="relative space-y-5">
        <span className="accent-pill">Open role</span>
        <CardTitle className="text-white text-2xl sm:text-3xl leading-tight tracking-tight">
          {job.title}
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-4 text-white/70">
          {job.salary && (
            <span className="flex items-center gap-2 text-sm font-medium">
              <PoundSterling className="h-4 w-4 text-white/60" />
              <span>{job.salary}</span>
            </span>
          )}
          <span className="text-sm">Posted {formatDate(job.created_at)}</span>
        </CardDescription>
      </CardHeader>
      <CardContent className="relative space-y-6">
        <p className="text-sm leading-relaxed text-white/70 line-clamp-4 md:line-clamp-5">
          {job.description}
        </p>
        <Link to={`/jobs/${job.id}`} className="inline-flex">
          <Button variant="outline" size="sm" className="px-5">
            View details
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
};
