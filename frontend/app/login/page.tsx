import { LoginForm } from "./login-form";

export default function LoginPage({
  searchParams,
}: {
  searchParams: { error?: string; next?: string };
}) {
  return (
    <main className="mx-auto flex max-w-md flex-col justify-center px-6 py-24">
      <h1 className="font-serif text-3xl font-semibold text-slate-900">Sign in</h1>
      <p className="mt-3 text-slate-600">
        Enter your email and we&apos;ll send you a link to sign in — no
        password to remember.
      </p>

      {searchParams.error ? (
        <p className="mt-6 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          That sign-in link didn&apos;t work — it may have expired. Request a
          new one below.
        </p>
      ) : null}

      <LoginForm next={searchParams.next} />
    </main>
  );
}
