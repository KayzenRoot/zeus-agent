import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import {
  Activity,
  ArrowUpRight,
  Bot,
  Cpu,
  Network,
  Sparkles,
  Terminal,
  Users,
  Zap,
} from "lucide-react";
import { H2 } from "@nous-research/ui/ui/components/typography/h2";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { api, type ProfileInfo } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Constellation — the signature "Dots-like" surface (EXP-002 #30).
 *
 * The orchestrator sits at the centre and every profile is a specialist in
 * orbit. Edges are the delegation graph; the inspector exposes the live facts
 * the runtime already knows (model, provider, skills, gateway). Activity
 * pulses are the visual contract for the event bus work tracked in #30 —
 * until that lands the topology is real, the motion is decorative, and the
 * footer says so.
 */

type AgentStatus = "active" | "idle" | "offline";

interface ConstellationNode {
  id: string;
  name: string;
  subtitle: string;
  status: AgentStatus;
  x: number;
  y: number;
  profile?: ProfileInfo;
}

const COLORS = ["#e8c27a", "#7dd3c7", "#a78bfa", "#f0a6a6", "#93c5fd", "#facc15"];

const DEMO_PROFILES: ProfileInfo[] = [
  {
    name: "research",
    path: "profiles/research",
    is_default: true,
    model: "deepseek-v4.1-flash",
    provider: "opencode-go",
    has_env: true,
    skill_count: 12,
    gateway_running: true,
    description: "Pesquisa, síntese e leitura de fontes.",
    description_auto: false,
    display_name: "Research",
    distribution_name: null,
    distribution_version: null,
    distribution_source: null,
    has_alias: false,
  },
  {
    name: "engineering",
    path: "profiles/engineering",
    is_default: false,
    model: "deepseek-v4.1-flash",
    provider: "opencode-go",
    has_env: true,
    skill_count: 18,
    gateway_running: false,
    description: "Código, arquivos e terminal.",
    description_auto: false,
    display_name: "Engineering",
    distribution_name: null,
    distribution_version: null,
    distribution_source: null,
    has_alias: false,
  },
  {
    name: "ops",
    path: "profiles/ops",
    is_default: false,
    model: null,
    provider: null,
    has_env: false,
    skill_count: 7,
    gateway_running: false,
    description: "Cron, integrações e saúde do sistema.",
    description_auto: false,
    display_name: "Ops",
    distribution_name: null,
    distribution_version: null,
    distribution_source: null,
    has_alias: false,
  },
];

function statusOf(profile: ProfileInfo): AgentStatus {
  if (profile.gateway_running) return "active";
  return profile.has_env ? "idle" : "offline";
}

function buildNodes(profiles: ProfileInfo[]): ConstellationNode[] {
  const source = profiles.length > 0 ? profiles.slice(0, 8) : DEMO_PROFILES;
  const n = source.length;

  if (n === 1) {
    return [
      {
        id: "orchestrator",
        name: "Orchestrator",
        subtitle: "master",
        status: "active",
        x: 50,
        y: 50,
      },
      {
        id: "solo",
        name: source[0].display_name ?? source[0].name,
        subtitle: source[0].description || "specialist",
        status: statusOf(source[0]),
        x: 50,
        y: 22,
        profile: source[0],
      },
    ];
  }

  const radiusX = 34;
  const radiusY = 31;

  return source.map((profile, index) => {
    const angle = (Math.PI * 2 * index) / n - Math.PI / 2;
    return {
      id: profile.name,
      name: profile.display_name ?? profile.name,
      subtitle: profile.description || "specialist",
      status: statusOf(profile),
      x: 50 + Math.cos(angle) * radiusX,
      y: 50 + Math.sin(angle) * radiusY,
      profile,
    };
  });
}

const STATUS_STYLES: Record<AgentStatus, { dot: string; label: string }> = {
  active: { dot: "bg-emerald-300", label: "active" },
  idle: { dot: "bg-amber-300", label: "idle" },
  offline: { dot: "bg-white/25", label: "offline" },
};

const ORCHESTRATOR_NODE: ConstellationNode = {
  id: "orchestrator",
  name: "Orchestrator",
  subtitle: "Zeus master — decomposes missions and assigns specialists",
  status: "active",
  x: 50,
  y: 50,
};

export default function ConstellationPage() {
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<ProfileInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getProfiles()
      .then((response) => {
        if (!alive) return;
        setProfiles(response.profiles ?? []);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Could not load profiles");
        setProfiles([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  const nodes = useMemo(() => buildNodes(profiles ?? []), [profiles]);
  const selected =
    selectedId === "orchestrator"
      ? ORCHESTRATOR_NODE
      : (nodes.find((node) => node.id === selectedId) ?? nodes[0] ?? ORCHESTRATOR_NODE);
  const usingDemo = (profiles?.length ?? 0) === 0;
  const active = nodes.filter((node) => node.status === "active").length;
  const skills = (profiles ?? []).reduce((total, profile) => total + profile.skill_count, 0);

  return (
    <div className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-[#05060a] text-[#f4efe3]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 45%, rgba(232,194,122,0.10) 0%, rgba(5,6,10,0) 70%), radial-gradient(45% 40% at 82% 10%, rgba(125,211,199,0.06) 0%, rgba(5,6,10,0) 75%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.16]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
          maskImage: "radial-gradient(ellipse at center, black 35%, transparent 75%)",
        }}
      />

      <div className="relative mx-auto flex w-full max-w-[1500px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-[#e8c27a]/80">
              <Network className="size-3.5" />
              Zeus orchestration
            </div>
            <H2 className="text-2xl font-semibold tracking-[-0.02em] text-[#f7f1e4] sm:text-3xl">
              Constellation
            </H2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-white/55">
              The orchestrator at the centre, specialists in orbit. Click a node to inspect the
              model, skills and runtime state behind it.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white/65">
              <span className="size-1.5 animate-pulse rounded-full bg-emerald-300" />
              {usingDemo ? "Reference topology" : "Live topology"}
            </span>
            <Button size="sm" onClick={() => navigate("/chat")} prefix={<Sparkles className="size-3.5" />}>
              New mission
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat icon={<Users className="size-4" />} label="Agents" value={String(nodes.length)} />
          <Stat icon={<Activity className="size-4" />} label="Active" value={String(active)} />
          <Stat icon={<Zap className="size-4" />} label="Skills" value={String(skills)} />
          <Stat
            icon={<Cpu className="size-4" />}
            label="Models"
            value={String(new Set((profiles ?? []).map((p) => p.model).filter(Boolean)).size)}
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
          <section className="relative overflow-hidden rounded-[1.4rem] border border-white/10 bg-white/[0.018]">
            <div className="relative h-[520px] sm:h-[600px]">
              <svg
                aria-hidden
                className="absolute inset-0 size-full"
                preserveAspectRatio="none"
                viewBox="0 0 100 100"
              >
                {nodes.map((node, index) => (
                  <g key={node.id}>
                    <line
                      className="zeus-constellation-edge"
                      style={{ animationDelay: `${index * 220}ms` }}
                      x1="50"
                      x2={node.x}
                      y1="50"
                      y2={node.y}
                      stroke={COLORS[index % COLORS.length]}
                      strokeOpacity="0.28"
                      strokeWidth="0.28"
                      vectorEffect="non-scaling-stroke"
                    />
                    <circle
                      cx={node.x}
                      cy={node.y}
                      fill={COLORS[index % COLORS.length]}
                      opacity="0.5"
                      r="0.55"
                    />
                  </g>
                ))}
              </svg>

              <button
                className="group absolute left-1/2 top-1/2 z-10 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2"
                onClick={() => setSelectedId("orchestrator")}
                type="button"
              >
                <span className="relative flex size-28 items-center justify-center rounded-full border border-[#e8c27a]/35 bg-[#0b0d13]/90 shadow-[0_0_0_10px_rgba(232,194,122,0.04),0_0_80px_rgba(232,194,122,0.18)] transition group-hover:border-[#e8c27a]/60">
                  <span className="absolute inset-2 rounded-full border border-white/10" />
                  <span className="absolute inset-0 animate-ping rounded-full border border-[#e8c27a]/20 [animation-duration:3.5s]" />
                  <Bot className="size-9 text-[#e8c27a]" />
                </span>
                <span className="rounded-full border border-white/10 bg-[#0b0d13]/80 px-3 py-1 text-center text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-[#f3dfb5]">
                  Orchestrator
                </span>
                <span className="text-[0.65rem] uppercase tracking-[0.18em] text-white/35">
                  master
                </span>
              </button>

              {nodes.map((node, index) => {
                const color = COLORS[index % COLORS.length];
                const isSelected = selected?.id === node.id;
                return (
                  <button
                    key={node.id}
                    className={cn(
                      "absolute z-10 flex w-32 -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2 text-center transition",
                      "hover:-translate-y-[calc(50%+2px)]",
                    )}
                    onClick={() => setSelectedId(node.id)}
                    style={{ left: `${node.x}%`, top: `${node.y}%` }}
                    type="button"
                  >
                    <span
                      className={cn(
                        "relative flex size-16 items-center justify-center rounded-2xl border bg-[#0a0c12]/90 shadow-lg transition",
                        isSelected ? "scale-105 border-white/35" : "border-white/10",
                      )}
                      style={{ boxShadow: `0 0 34px ${color}22` }}
                    >
                      <span
                        className="absolute inset-0 rounded-2xl opacity-55"
                        style={{ background: `radial-gradient(circle at 50% 20%, ${color}26, transparent 65%)` }}
                      />
                      <Terminal className="size-6" style={{ color }} />
                      <span
                        className={cn(
                          "absolute -right-1 -top-1 size-3 rounded-full border-2 border-[#05060a]",
                          STATUS_STYLES[node.status].dot,
                        )}
                      />
                    </span>
                    <span className="max-w-full truncate text-xs font-semibold text-white/85">
                      {node.name}
                    </span>
                    <span className="max-w-full truncate text-[0.62rem] uppercase tracking-[0.14em] text-white/35">
                      {STATUS_STYLES[node.status].label}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/10 px-4 py-3 text-[0.68rem] text-white/40">
              <div className="flex flex-wrap items-center gap-4">
                <Legend color="bg-emerald-300" label="active" />
                <Legend color="bg-amber-300" label="idle" />
                <Legend color="bg-white/25" label="offline" />
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-px w-6 bg-[#e8c27a]/50" /> delegation
                </span>
              </div>
              <span>
                {usingDemo
                  ? "Demo topology — connect profiles to see your own agents."
                  : "Motion is illustrative until the live event bus lands (#30)."}
              </span>
            </div>
          </section>

          <aside className="rounded-[1.4rem] border border-white/10 bg-white/[0.025] p-5">
            {selected ? (
              <>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-white/35">
                      Inspector
                    </div>
                    <div className="mt-1 text-lg font-semibold text-white/90">{selected.name}</div>
                    <div className="mt-1 text-xs leading-5 text-white/45">{selected.subtitle}</div>
                  </div>
                  <Badge className="border-white/10 bg-white/5 text-white/60">
                    {selected.profile ? STATUS_STYLES[selected.status].label : "master"}
                  </Badge>
                </div>

                <div className="mt-5 grid gap-2">
                  <InspectorRow label="Model" value={selected.profile?.model ?? "auto"} />
                  <InspectorRow label="Provider" value={selected.profile?.provider ?? "Zeus router"} />
                  <InspectorRow label="Skills" value={String(selected.profile?.skill_count ?? 0)} />
                  <InspectorRow
                    label="Gateway"
                    value={selected.profile?.gateway_running ? "running" : "stopped"}
                  />
                </div>

                {selected.profile ? (
                  <>
                    <div className="mt-5 rounded-xl border border-white/10 bg-black/20 p-3 text-[0.7rem] leading-5 text-white/40">
                      <span className="text-white/55">Profile path</span>
                      <div className="mt-1 truncate font-mono text-white/70">{selected.profile.path}</div>
                    </div>
                    <Button
                      className="mt-4 w-full"
                      ghost
                      onClick={() => navigate("/profiles")}
                      prefix={<ArrowUpRight className="size-3.5" />}
                    >
                      Open profiles
                    </Button>
                  </>
                ) : (
                  <div className="mt-5 rounded-xl border border-[#e8c27a]/20 bg-[#e8c27a]/5 p-3 text-[0.72rem] leading-5 text-[#e8c27a]/80">
                    The orchestrator decomposes a mission, picks specialists and keeps the budget.
                    Live delegation tracing is tracked in #30.
                  </div>
                )}

                {error ? (
                  <p className="mt-4 text-[0.7rem] leading-5 text-red-300/70">
                    Could not load profiles: {error}
                  </p>
                ) : null}
              </>
            ) : (
              <p className="text-sm text-white/50">No agents yet.</p>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.025] px-4 py-3">
      <div className="flex items-center gap-2 text-[0.65rem] uppercase tracking-[0.18em] text-white/35">
        {icon}
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold tracking-tight text-white/85">{value}</div>
    </div>
  );
}

function InspectorRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2 text-xs">
      <span className="text-white/35">{label}</span>
      <span className="truncate font-medium text-white/75">{value}</span>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={cn("size-1.5 rounded-full", color)} />
      {label}
    </span>
  );
}
