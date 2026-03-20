'use client';

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiLogin, apiLogout, apiRegister } from "../lib/api";
import { getToken } from "../lib/auth";

function Field(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-sm text-zinc-400">{props.label}</div>
      <input
        className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-zinc-100 outline-none focus:border-sky-400"
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        type={props.type ?? "text"}
        placeholder={props.placeholder}
      />
    </label>
  );
}

export default function Home() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setToken(getToken());
  }, []);

  useEffect(() => {
    if (token) router.push("/app");
  }, [token, router]);

  const title = useMemo(() => (mode === "login" ? "Login" : "Create account"), [mode]);

  async function onSubmit() {
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") {
        await apiLogin(username, password);
      } else {
        await apiRegister(username, password);
      }
      setToken(getToken());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <header className="mb-10">
          <div className="text-xs font-semibold tracking-[0.18em] text-sky-300/80">
            METABOLIC DIGITAL TWIN
          </div>
          <h1 className="mt-2 text-5xl font-bold tracking-tight">Oxia</h1>
          <p className="mt-3 max-w-2xl text-zinc-400">
            Snap your meal. See your next 3 hours of glucose, inflammation, and cognitive focus — and get concrete swaps to optimize it.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <section className="rounded-2xl border border-zinc-800 bg-gradient-to-b from-sky-500/5 to-transparent p-6">
            <div className="text-sm font-semibold text-zinc-300">What you get</div>
            <div className="mt-4 space-y-3 text-zinc-400">
              <div>• Your Next 3 Hours timeline (moment of truth)</div>
              <div>• Metric-aware personas in first-person</div>
              <div>• “Make It Better” quantified meal swaps</div>
              <div>• In-context chatbot grounded in your dashboard</div>
            </div>
            <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">
              Educational estimates only. Not medical advice.
            </div>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-6">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-zinc-300">{title}</div>
              {token ? (
                <button
                  className="rounded-xl border border-zinc-800 px-4 py-2 text-sm hover:bg-zinc-900"
                  onClick={() => {
                    apiLogout();
                    setToken(null);
                  }}
                >
                  Logout
                </button>
              ) : null}
            </div>

            <div className="mt-4 space-y-4">
              <Field
                label="Username"
                value={username}
                onChange={setUsername}
                placeholder="e.g., adip7"
              />
              <Field
                label="Password"
                value={password}
                onChange={setPassword}
                type="password"
                placeholder="••••••••"
              />

              {error ? (
                <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
                  {error}
                </div>
              ) : null}

              <button
                disabled={busy || !username || !password}
                onClick={onSubmit}
                className="w-full rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-4 py-3 font-semibold text-zinc-950 disabled:opacity-60"
              >
                {busy ? "Working..." : mode === "login" ? "Login to Oxia" : "Create & Enter"}
              </button>

              <div className="pt-2 text-center text-sm text-zinc-500">
                {mode === "login" ? (
                  <>
                    No account?{" "}
                    <button className="text-sky-300 hover:underline" onClick={() => setMode("register")}>
                      Create one
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{" "}
                    <button className="text-sky-300 hover:underline" onClick={() => setMode("login")}>
                      Login
                    </button>
                  </>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
