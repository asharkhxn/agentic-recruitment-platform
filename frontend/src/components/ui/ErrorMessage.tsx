import { AlertCircle } from "lucide-react";
import { Card, CardContent } from "./Card";

interface ErrorMessageProps {
  message?: string;
  title?: string;
}

export const ErrorMessage = ({
  message = "Something went wrong. Please try again.",
  title = "Error",
}: ErrorMessageProps) => {
  return (
    <Card className="border-rose-500/40 bg-rose-500/10">
      <CardContent className="flex items-start gap-3 px-6 py-5">
        <AlertCircle className="h-5 w-5 text-rose-300" />
        <div>
          <h3 className="font-semibold text-rose-200">{title}</h3>
          <p className="text-sm text-rose-100/80">{message}</p>
        </div>
      </CardContent>
    </Card>
  );
};
