import { useEffect, useId, useMemo, useState, type ReactNode } from "react";
import { useNavigate } from "react-router";
import {
  Activity,
  ArrowUpRight,
  Cpu,
  Network,
  Sparkles,
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

type AgentStatus = "active" | "working" | "idle" | "offline";

interface ProfileActivity {
  count: number;
  lastActiveMs: number | null;
}

interface ConstellationNode {
  id: string;
  name: string;
  subtitle: string;
  status: AgentStatus;
  x: number;
  y: number;
  profile?: ProfileInfo;
  activity?: ProfileActivity;
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

const RECENT_ACTIVITY_MS = 5 * 60_000;

function statusOf(
  profile: ProfileInfo,
  activity?: ProfileActivity,
): AgentStatus {
  if (profile.gateway_running) return "active";
  if (
    activity?.lastActiveMs &&
    Date.now() - activity.lastActiveMs < RECENT_ACTIVITY_MS
  ) {
    return "active";
  }
  return profile.has_env ? "idle" : "offline";
}

function buildNodes(
  profiles: ProfileInfo[],
  activity: Record<string, ProfileActivity> = {},
): ConstellationNode[] {
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
        status: statusOf(source[0], activity[source[0].name]),
        x: 50,
        y: 22,
        profile: source[0],
        activity: activity[source[0].name],
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
      status: statusOf(profile, activity[profile.name]),
      x: 50 + Math.cos(angle) * radiusX,
      y: 50 + Math.sin(angle) * radiusY,
      profile,
      activity: activity[profile.name],
    };
  });
}

const STATUS_STYLES: Record<AgentStatus, { dot: string; label: string }> = {
  active: { dot: "bg-emerald-300", label: "active" },
  working: { dot: "bg-sky-300", label: "working" },
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

/** Curved delegation path from the orchestrator (50,50) to a specialist. */
function edgePath(node: ConstellationNode): string {
  const mx = (50 + node.x) / 2 + (node.y - 50) * 0.14;
  const my = (50 + node.y) / 2 - (node.x - 50) * 0.14;
  return `M 50 50 Q ${mx.toFixed(2)} ${my.toFixed(2)} ${node.x.toFixed(2)} ${node.y.toFixed(2)}`;
}

/**
 * A Dots-style avatar: a colored bubble with a face. Eyes encode the live
 * state (open = active, half-lidded = idle, crossed = offline) and some
 * specialists wear glasses, matching ChatGPT Dots' customizable avatars.
 */
function DotAvatar({
  color,
  status,
  size = 64,
  accessory = false,
}: {
  color: string;
  status: AgentStatus;
  size?: number;
  accessory?: boolean;
}) {
  return (
    <svg
      aria-hidden
      className="drop-shadow-[0_0_16px_rgba(232,194,122,0.18)]"
      height={size}
      viewBox="0 0 64 64"
      width={size}
    >
      <circle cx="32" cy="32" r="28" fill={`${color}1f`} />
      <circle cx="32" cy="32" r="21" fill={color} opacity="0.92" />
      <ellipse cx="24" cy="23" fill="#ffffff" opacity="0.18" rx="8" ry="4.5" />
      {status === "offline" ? (
        <g stroke="#0b0d13" strokeLinecap="round" strokeWidth="2">
          <path d="M22 30l6 4M28 30l-6 4" />
          <path d="M36 30l6 4M42 30l-6 4" />
        </g>
      ) : status === "idle" ? (
        <g stroke="#0b0d13" strokeLinecap="round" strokeWidth="2">
          <path d="M22 31h7" />
          <path d="M35 31h7" />
        </g>
      ) : (
        <g>
          <circle cx="25" cy="30" fill="#0b0d13" r="2.4" />
          <circle cx="39" cy="30" fill="#0b0d13" r="2.4" />
          <circle cx="25.8" cy="29.2" fill="#ffffff" r="0.7" />
          <circle cx="39.8" cy="29.2" fill="#ffffff" r="0.7" />
        </g>
      )}
      {status !== "offline" ? (
        <path
          d="M27 39c2.2 2 7.8 2 10 0"
          fill="none"
          opacity="0.8"
          stroke="#0b0d13"
          strokeLinecap="round"
          strokeWidth="1.8"
        />
      ) : null}
      {accessory ? (
        <g fill="none" opacity="0.9" stroke="#0b0d13" strokeWidth="1.4">
          <circle cx="25" cy="30" r="5.6" />
          <circle cx="39" cy="30" r="5.6" />
          <path d="M30.6 30h2.8" />
        </g>
      ) : null}
    </svg>
  );
}

function formatLastActive(ms: number | null): string {
  if (!ms) return "no sessions";
  const diff = Date.now() - ms;
  if (diff < 60_000) return "just now";
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function InspectorPanel({
  error,
  onOpenProfiles,
  selected,
}: {
  error: string | null;
  onOpenProfiles: () => void;
  selected: ConstellationNode;
}) {
  return (
    <aside className="rounded-[1.4rem] border border-white/10 bg-white/[0.025] p-5">
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
          label="Sessions"
          value={selected.profile ? String(selected.activity?.count ?? 0) : "—"}
        />
        <InspectorRow
          label="Last active"
          value={
            selected.profile
              ? formatLastActive(selected.activity?.lastActiveMs ?? null)
              : "now"
          }
        />
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
            onClick={onOpenProfiles}
            prefix={<ArrowUpRight className="size-3.5" />}
          >
            Open profiles
          </Button>
        </>
      ) : (
        <div className="mt-5 rounded-xl border border-[#e8c27a]/20 bg-[#e8c27a]/5 p-3 text-[0.72rem] leading-5 text-[#e8c27a]/80">
          The orchestrator decomposes a mission, picks specialists and keeps the budget. Live
          delegation tracing is tracked in #30.
        </div>
      )}

      {error ? (
        <p className="mt-4 text-[0.7rem] leading-5 text-red-300/70">
          Could not load profiles: {error}
        </p>
      ) : null}
    </aside>
  );
}

export default function ConstellationPage() {
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<ProfileInfo[] | null>(null);
  const [activity, setActivity] = useState<Record<string, ProfileActivity>>({});
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [activeTick, setActiveTick] = useState(0);
  const uid = useId().replace(/:/g, "");

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

  // Real activity per profile: session count + the newest last_active. This is
  // what turns a gateway-running dot into a genuinely "active" one; the
  // delegation pulse stays illustrative until the event bus (#30).
  useEffect(() => {
    if (!profiles?.length) return;
    let alive = true;

    const load = () => {
      void Promise.all(
        profiles.map(async (profile) => {
          try {
            const page = await api.getSessions(20, 0, profile.name);
            const sessions = page.sessions ?? [];
            const lastActiveMs =
              sessions.reduce(
                (max, session) => Math.max(max, (session.last_active ?? 0) * 1000),
                0,
              ) || null;
            return [profile.name, { count: sessions.length, lastActiveMs }] as const;
          } catch {
            return [profile.name, { count: 0, lastActiveMs: null }] as const;
          }
        }),
      ).then((entries) => {
        if (alive) setActivity(Object.fromEntries(entries));
      });
    };

    load();
    const timer = window.setInterval(load, 20_000);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [profiles]);

  const nodes = useMemo(
    () => buildNodes(profiles ?? [], activity),
    [profiles, activity],
  );

  // Demo delegation: until the event bus (#30) is wired, the orchestrator hands
  // work to one specialist at a time so the energy line and the avatar visibly
  // sync. Reduced-motion users keep the static topology.
  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const timer = window.setInterval(() => setActiveTick(tick => tick + 1), 4200);
    return () => window.clearInterval(timer);
  }, []);

  const liveNodes = useMemo(() => {
    const specialists = nodes.filter(node => node.profile && node.status !== "offline");
    const workingId = specialists.length
      ? specialists[activeTick % specialists.length].id
      : null;
    return nodes.map(node =>
      node.id === workingId ? { ...node, status: "working" as const } : node,
    );
  }, [nodes, activeTick]);

  const selected =
    selectedId === "orchestrator"
      ? ORCHESTRATOR_NODE
      : (liveNodes.find((node) => node.id === selectedId) ?? liveNodes[0] ?? ORCHESTRATOR_NODE);
  const working = liveNodes.find((node) => node.status === "working") ?? null;
  const usingDemo = (profiles?.length ?? 0) === 0;
  const active = liveNodes.filter(
    (node) => node.status === "active" || node.status === "working",
  ).length;
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
          <Stat icon={<Users className="size-4" />} label="Agents" value={String(liveNodes.length)} />
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
                <defs>
                  {liveNodes.map((node, index) => (
                    <linearGradient
                      gradientUnits="userSpaceOnUse"
                      id={`${uid}-edge-${index}`}
                      key={`${node.id}-gradient`}
                      x1="50"
                      x2={node.x}
                      y1="50"
                      y2={node.y}
                    >
                      <stop stopColor="#e8c27a" />
                      <stop offset="1" stopColor={COLORS[index % COLORS.length]} />
                    </linearGradient>
                  ))}
                </defs>
                {liveNodes.map((node, index) => {
                  const color = COLORS[index % COLORS.length];
                  const d = edgePath(node);
                  const active =
                    node.status === "active" ||
                    node.status === "working" ||
                    selected?.id === node.id;
                  const duration = active ? "2.4s" : "5.6s";

                  return (
                    <g key={node.id}>
                      <path
                        d={d}
                        fill="none"
                        stroke={color}
                        strokeOpacity={active ? 0.2 : 0.08}
                        strokeWidth={active ? 3.6 : 2.2}
                        style={{ filter: "blur(1.4px)" }}
                        vectorEffect="non-scaling-stroke"
                      />
                      <path
                        d={d}
                        fill="none"
                        stroke={`url(#${uid}-edge-${index})`}
                        strokeOpacity={active ? 0.7 : 0.26}
                        strokeWidth={active ? 1.1 : 0.55}
                        vectorEffect="non-scaling-stroke"
                      />
                      <path
                        className="zeus-energy-flow"
                        d={d}
                        fill="none"
                        stroke={color}
                        strokeDasharray="1.4 4"
                        strokeLinecap="round"
                        strokeOpacity={active ? 0.98 : 0.5}
                        strokeWidth={active ? 1.2 : 0.7}
                        style={{
                          animationDelay: `${index * 180}ms`,
                          animationDuration: duration,
                          filter: `drop-shadow(0 0 2px ${color})`,
                        }}
                        vectorEffect="non-scaling-stroke"
                      />
                      <circle cx={node.x} cy={node.y} fill={color} opacity="0.6" r="0.7" />
                      {[0, 1].map(packet => (
                        <circle
                          fill={color}
                          key={packet}
                          opacity={active ? 0.98 : 0.6}
                          r={active ? 1.25 : 0.8}
                          style={{ filter: `drop-shadow(0 0 3px ${color})` }}
                        >
                          <animateMotion
                            begin={`${index * 0.3 + packet * 0.45}s`}
                            dur={duration}
                            path={d}
                            repeatCount="indefinite"
                          />
                        </circle>
                      ))}
                    </g>
                  );
                })}
              </svg>

              <button
                className="group absolute left-1/2 top-1/2 z-10 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-2"
                onClick={() => setSelectedId("orchestrator")}
                type="button"
              >
                <span className="relative flex size-28 items-center justify-center rounded-full border border-[#e8c27a]/35 bg-[#0b0d13]/90 shadow-[0_0_0_10px_rgba(232,194,122,0.04),0_0_80px_rgba(232,194,122,0.18)] transition group-hover:border-[#e8c27a]/60">
                  <span className="absolute inset-2 rounded-full border border-white/10" />
                  <span className="absolute inset-0 animate-ping rounded-full border border-[#e8c27a]/20 [animation-duration:3.5s]" />
                  <DotAvatar accessory color="#e8c27a" size={76} status="active" />
                </span>
                <span className="rounded-full border border-white/10 bg-[#0b0d13]/80 px-3 py-1 text-center text-[0.7rem] font-semibold uppercase tracking-[0.18em] text-[#f3dfb5]">
                  Orchestrator
                </span>
                <span className="text-[0.65rem] uppercase tracking-[0.18em] text-white/35">
                  master
                </span>
              </button>

              {liveNodes.map((node, index) => {
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
                        "relative flex size-16 items-center justify-center rounded-full border bg-[#0a0c12]/70 shadow-lg transition",
                        isSelected ? "scale-105 border-white/35" : "border-white/10",
                        (isSelected ||
                          node.status === "active" ||
                          node.status === "working") &&
                          "zeus-node-active",
                      )}
                      style={{ boxShadow: `0 0 34px ${color}22` }}
                    >
                      <span
                        className="absolute inset-0 rounded-full opacity-55"
                        style={{ background: `radial-gradient(circle at 50% 20%, ${color}26, transparent 65%)` }}
                      />
                      <DotAvatar
                        accessory={index % 4 === 0}
                        color={color}
                        size={56}
                        status={node.status}
                      />
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
                <Legend color="bg-sky-300" label="working" />
                <Legend color="bg-amber-300" label="idle" />
                <Legend color="bg-white/25" label="offline" />
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-px w-6 bg-[#e8c27a]/50" /> delegation
                </span>
              </div>
              <span>
                {usingDemo
                  ? "Demo topology — connect profiles to see your own agents."
                  : working
                    ? `Orchestrator → ${working.name} · activity demo until the event bus lands (#30).`
                    : "Motion is illustrative until the live event bus lands (#30)."}
              </span>
            </div>
          </section>

          <InspectorPanel
            error={error}
            onOpenProfiles={() => navigate("/profiles")}
            selected={selected}
          />
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
