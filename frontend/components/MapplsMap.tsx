"use client";
import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import type { Violation } from "@/lib/types";

export default function MapplsMap({ violations }: { violations: Violation[] }) {
  const mapRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const markersRef = useRef<any[]>([]);

  const initMap = () => {
    if (typeof window !== "undefined" && (window as any).mappls && containerRef.current && !mapRef.current) {
      try {
        mapRef.current = new (window as any).mappls.Map(containerRef.current, {
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

  const apiKey = process.env.NEXT_PUBLIC_MAPPLS_API_KEY || "96eecbc8903abee5507fe87ff2af70a6";

  return (
    <>
      <Script 
        src={`https://apis.mappls.com/advancedmaps/api/${apiKey}/map_sdk?layer=vector&v=3.0`}
        strategy="afterInteractive"
        onLoad={initMap}
      />
      <div className="card h-96 w-full overflow-hidden p-0 rounded-lg border border-slate-700 mt-8 relative">
        <div ref={containerRef} className="h-full w-full bg-slate-800 flex items-center justify-center">
            {!loaded && <span className="text-slate-500 animate-pulse">Loading Mappls 3D Map SDK...</span>}
        </div>
      </div>
    </>
  );
}
