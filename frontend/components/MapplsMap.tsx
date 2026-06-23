"use client";
import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import type { Violation } from "@/lib/types";

export default function MapplsMap({ violations }: { violations: Violation[] }) {
  const mapRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    (window as any).initMappls = () => {
      if (typeof window !== "undefined" && (window as any).mappls && document.getElementById("mappls-map") && !mapRef.current) {
        try {
          mapRef.current = new (window as any).mappls.Map("mappls-map", {
            center: [12.9172, 77.6228], // Default to Silk Board
            zoomControl: true,
            location: true,
            zoom: 12,
          });
          setLoaded(true);
        } catch (err) {
          console.error("Mappls Init Error:", err);
        }
      }
    };
  }, []);

  useEffect(() => {
    if (!loaded || !mapRef.current) return;

    // Clear old markers
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    // Add new markers
    violations.forEach((v) => {
      if (v.location_lat && v.location_lng) {
        const marker = new (window as any).mappls.Marker({
          map: mapRef.current,
          position: { lat: v.location_lat, lng: v.location_lng },
          title: v.violation_type,
          description: v.location_name || "Unknown Location",
        });
        markersRef.current.push(marker);
      }
    });
  }, [violations, loaded]);

  const apiKey = process.env.NEXT_PUBLIC_MAPPLS_API_KEY || "";

  return (
    <>
      <Script 
        src={`https://apis.mappls.com/advancedmaps/api/${apiKey}/map_sdk?layer=vector&v=3.0&callback=initMappls`}
        strategy="afterInteractive"
      />
      <div className="card h-96 w-full overflow-hidden p-0 rounded-lg border border-slate-700 mt-8 relative">
        {!loaded && (
          <div className="absolute inset-0 bg-slate-800 flex items-center justify-center z-10">
            <span className="text-slate-500 animate-pulse">Loading Mappls 3D Map SDK...</span>
          </div>
        )}
        <div id="mappls-map" ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '384px' }} />
      </div>
    </>
  );
}
