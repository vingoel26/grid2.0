export default function Badge({ label, className }: { label: string; className?: string }) {
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${className || ""}`}>
      {label}
    </span>
  );
}
