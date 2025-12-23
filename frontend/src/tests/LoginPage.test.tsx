import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LoginPage } from "@/pages/LoginPage";

const queryClient = new QueryClient();

const MockedLoginPage = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  </QueryClientProvider>
);

describe("LoginPage", () => {
  it("renders login form", () => {
    render(<MockedLoginPage />);

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("shows validation for empty fields", async () => {
    render(<MockedLoginPage />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    fireEvent.click(submitButton);

    // HTML5 validation will prevent submission
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toBeRequired();
  });
});
