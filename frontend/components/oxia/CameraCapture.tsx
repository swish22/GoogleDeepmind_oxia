"use client";

import { useEffect, useRef, useState } from "react";

export default function CameraCapture(props: {
  onCaptured: (file: File) => void;
}) {
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      return;
    }

    let cancelled = false;
    async function start() {
      setError(null);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
      }
    }

    start();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  async function capture() {
    if (!videoRef.current) return;
    if (!streamRef.current) return;

    setBusy(true);
    setError(null);

    try {
      const video = videoRef.current;
      const w = video.videoWidth || 1280;
      const h = video.videoHeight || 720;

      // Downscale slightly to keep compute + upload smaller.
      const maxDim = 1024;
      const scale = Math.min(1, maxDim / Math.max(w, h));
      const cw = Math.floor(w * scale);
      const ch = Math.floor(h * scale);

      const canvas = document.createElement("canvas");
      canvas.width = cw;
      canvas.height = ch;
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Canvas not supported.");

      ctx.drawImage(video, 0, 0, cw, ch);

      const blob: Blob | null = await new Promise((resolve) => {
        canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9);
      });
      if (!blob) throw new Error("Failed to capture image.");

      const file = new File([blob], "meal.jpg", { type: "image/jpeg" });
      props.onCaptured(file);

      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-zinc-300">Camera snapshot (low compute)</div>
        <button
          type="button"
          onClick={() => setEnabled((v) => !v)}
          className="rounded-xl border border-zinc-800 px-4 py-2 text-sm hover:bg-zinc-900"
        >
          {enabled ? "Stop" : "Start"}
        </button>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </div>
      ) : null}

      {enabled ? (
        <div className="space-y-3">
          <video
            ref={videoRef}
            playsInline
            muted
            className="w-full rounded-xl border border-zinc-800 bg-black/30"
          />
          <button
            type="button"
            disabled={busy}
            onClick={capture}
            className="w-full rounded-xl bg-gradient-to-r from-sky-400 to-indigo-500 px-4 py-3 font-semibold text-zinc-950 disabled:opacity-60"
          >
            {busy ? "Capturing..." : "Capture photo"}
          </button>
        </div>
      ) : null}

      {previewUrl ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold tracking-[0.14em] text-zinc-500">Captured preview</div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={previewUrl} alt="Captured meal preview" className="w-full rounded-xl border border-zinc-800" />
        </div>
      ) : null}
    </div>
  );
}

