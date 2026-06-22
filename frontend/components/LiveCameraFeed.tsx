"use client";
import { useState } from "react";

export default function LiveCameraFeed() {
  const [status, setStatus] = useState<"idle" | "starting" | "running">("idle");
  const [error, setError] = useState<string | null>(null);

  const startPipeline = async () => {
    setStatus("starting");
    setError(null);
    try {
      // Create FormData as expected by the FastAPI backend
      const formData = new FormData();
      // Using an absolute path is required for the backend script, 
      // but assuming the user drops it in frontend/public, we pass the local windows path.
      // We will hardcode it to look for a generic demo.mp4 in the frontend/public folder.
      const videoPath = "C:\\Users\\HP\\grid\\gridlock\\frontend\\public\\demo.mp4";
      formData.append("source", videoPath);
      formData.append("camera_id", "BTP_SILK_BOARD_02");
      formData.append("frame_skip", "2");

      const res = await fetch("http://localhost:8001/stream/start", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to start pipeline");
      }
      
      setStatus("running");
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Could not connect to ML Server. Is it running on port 8001?");
      setStatus("idle");
    }
  };

  return (
    <div className="card h-96 w-full flex flex-col p-4 rounded-lg border border-slate-700 mt-8 relative bg-slate-900">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span className="h-2 w-2 bg-red-500 rounded-full animate-pulse"></span>
          Live CCTV Feed (Silk Board Flyover)
        </h3>
        <button
          onClick={startPipeline}
          disabled={status !== "idle"}
          className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
            status === "idle" 
              ? "bg-blue-600 hover:bg-blue-500 text-white" 
              : "bg-slate-700 text-slate-400 cursor-not-allowed"
          }`}
        >
          {status === "idle" ? "Start AI Detection" : status === "starting" ? "Starting..." : "Pipeline Running"}
        </button>
      </div>

      <div className="flex-1 relative bg-black rounded overflow-hidden flex items-center justify-center border border-slate-800">
        <video 
          src="/demo.mp4" 
          autoPlay 
          loop 
          muted 
          controls 
          className="w-full h-full object-contain"
          onError={(e) => {
            // If demo.mp4 doesn't exist yet, show a fallback message
            (e.target as HTMLVideoElement).style.display = "none";
            document.getElementById("video-fallback")?.classList.remove("hidden");
          }}
        />
        <div id="video-fallback" className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 hidden px-6 text-center">
          <svg className="w-12 h-12 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="mb-2 text-white font-medium">No Video Found</p>
          <p className="text-sm">Please place a video file named <code className="bg-slate-800 px-1 py-0.5 rounded text-blue-400">demo.mp4</code> inside the <br/><code className="bg-slate-800 px-1 py-0.5 rounded">gridlock/frontend/public/</code> folder.</p>
        </div>
      </div>

      {error && (
        <div className="mt-3 text-red-400 text-sm bg-red-950/30 p-2 rounded border border-red-900/50">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}
