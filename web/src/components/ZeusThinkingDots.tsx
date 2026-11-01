import { cn } from "@/lib/utils";

/**
 * ChatGPT-style "agent is working" indicator: three staggered pulsing dots in
 * a floating glass pill. Rendered over the chat terminal while the agent is
 * producing output (driven by ChatPage's PTY activity detector).
 */
export function ZeusThinkingDots({
  label = "Zeus is working",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      aria-live="polite"
      aria-busy="true"
      className={cn(
        "zeus-glass pointer-events-none select-none",
        "inline-flex items-center gap-2.5",
        "rounded-full border border-white/15",
        "bg-black/45 px-4 py-2",
        "shadow-[0_8px_32px_rgba(0,0,0,0.45)]",
        "animate-zeus-rise",
        className,
      )}
    >
      <span className="flex items-center gap-1" aria-hidden>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="zeus-dot inline-block h-1.5 w-1.5 rounded-full bg-white/85"
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        ))}
      </span>
      <span className="text-xs font-medium tracking-wide text-white/80">
        {label}
      </span>
    </div>
  );
}
