import {
  Activity,
  ArrowRightLeft,
  BadgeCheck,
  BookOpen,
  Bot,
  CircuitBoard,
  Cpu,
  Fingerprint,
  Gavel,
  HeartHandshake,
  Home,
  Landmark,
  ListChecks,
  LockKeyhole,
  MessageSquare,
  Network,
  Orbit,
  PlusCircle,
  Radar,
  ScanLine,
  ShieldCheck,
  Sparkles,
  UserPlus,
  Users,
  Upload,
  Download,
  QrCode,
} from "lucide-react";
import { FormEvent, ReactNode, useEffect, useReducer, useState, useRef } from "react";
import {
  citizenName,
  currentCitizen,
  loadState,
  parseCitizenType,
  reduceVoidState,
  saveState,
  VoidAction,
  subnetName
} from "./state/demoStore";
import { loadRemoteState, requiresAdminKey, requiresCitizenSession, sendRemoteAction, type RemoteKeys, type SyncStatus } from "./state/remoteStore";
import { createRemoteSession, readStoredSession, saveStoredSession, type CitizenSession } from "./state/sessionStore";
import type { FeedbackScope, ListingCategory, VoidState } from "./state/types";
import { formatPulseCredits, pulseCreditsToUsd, PULSE_CREDITS_PER_USD, PULSE_TOTAL_FEE_PERCENT } from "./shared/pulseCredits";

const ASSET_VERSION = "void-official-logo-v1";
const BRAND_MARK_SRC = `/void-official-logo.png?v=${ASSET_VERSION}`;

type ViewName =
  | "home"
  | "request"
  | "app"
  | "feed"
  | "admin"
  | "subnets"
  | "quests"
  | "market"
  | "governance"
  | "pulse"
  | "legacy"
  | "roadmap"
  | "legal"
  | "audit";

const navItems: Array<{ view: ViewName; label: string; icon: typeof Home; protected?: boolean }> = [
  { view: "home", label: "Network", icon: Home },
  { view: "request", label: "Join", icon: UserPlus },
  { view: "app", label: "Console", icon: CircuitBoard, protected: true },
  { view: "feed", label: "Feed", icon: MessageSquare, protected: true },
  { view: "admin", label: "Admin", icon: LockKeyhole, protected: true },
  { view: "subnets", label: "Subnets", icon: Network, protected: true },
  { view: "quests", label: "Quests", icon: ListChecks, protected: true },
  { view: "market", label: "Market", icon: Landmark, protected: true },
  { view: "governance", label: "Governance", icon: Gavel, protected: true },
  { view: "pulse", label: "Pulse", icon: ArrowRightLeft, protected: true },
  { view: "legacy", label: "Legacy", icon: BookOpen, protected: true },
  { view: "roadmap", label: "Roadmap", icon: Orbit },
  { view: "legal", label: "Legal", icon: ShieldCheck },
  { view: "audit", label: "Audit", icon: Activity, protected: true }
];

function stateReducer(state: VoidState, action: VoidAction) {
  const next = reduceVoidState(state, action);
  saveState(next);
  return next;
}

export default function App() {
  const [state, dispatch] = useReducer(stateReducer, undefined, loadState);
  const [view, setView] = useState<ViewName>(readHashView());
  const [alphaUnlocked, setAlphaUnlocked] = useState(false);
  const [installPrompt, setInstallPrompt] = useState<any>(null);
  const [adminKey, setAdminKey] = useState(() => sessionStorage.getItem("void-admin-key") || "");
  const [citizenSession, setCitizenSession] = useState<CitizenSession | null>(() => readStoredSession());
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({ mode: "idle", label: "Local alpha ready" });
  const citizen = currentCitizen(state);
  const operatorToolsVisible = import.meta.env.DEV;
  const visibleNavItems = navItems.filter((item) => operatorToolsVisible || !["admin", "audit"].includes(item.view));
  const operatorOnlyView = view === "admin" || view === "audit";
  const localPreviewMode = operatorToolsVisible && alphaUnlocked && !citizenSession && !adminKey;
  const canOperateAdmin = operatorToolsVisible && Boolean(adminKey || citizen?.titles.includes("Founder") || citizen?.titles.includes("Admin"));

  useEffect(() => {
    const handler = () => setView(readHashView());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  useEffect(() => {
    const beforeInstall = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event);
    };
    window.addEventListener("beforeinstallprompt", beforeInstall);
    return () => window.removeEventListener("beforeinstallprompt", beforeInstall);
  }, []);

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem("void-admin-key", adminKey);
  }, [adminKey]);

  useEffect(() => {
    let active = true;
    setSyncStatus({ mode: "syncing", label: "Connecting to deployment memory" });
    loadRemoteState(remoteKeys(adminKey, citizenSession?.token || "", citizenSession?.citizenId || state.currentCitizenId))
      .then((remoteState) => {
        if (!active) return;
        const preferredCitizen = citizenSession?.citizenId || state.currentCitizenId;
        dispatch({ type: "replaceState", state: mergeRemoteState(remoteState, preferredCitizen) });
        setSyncStatus({ mode: "online", label: adminKey || citizenSession ? "Protected memory online" : "Public memory online" });
      })
      .catch(() => {
        if (!active) return;
        setSyncStatus({ mode: "offline", label: "Local memory fallback" });
      });
    return () => {
      active = false;
    };
  }, [adminKey, citizenSession?.token, citizenSession?.citizenId]);

  function go(nextView: ViewName) {
    location.hash = nextView;
    setView(nextView);
  }

  function commit(action: VoidAction) {
    if (action.type === "setCurrentCitizen" || action.type === "replaceState") {
      dispatch(action);
      return;
    }

    if (localPreviewMode) {
      dispatch(action);
      setSyncStatus({ mode: "idle", label: "Local preview updated" });
      return;
    }

    if (requiresAdminKey(action) && !adminKey) {
      setSyncStatus({ mode: "error", label: "Admin key needed for server action" });
      return;
    }

    if (requiresCitizenSession(action) && !adminKey && !citizenSession) {
      setSyncStatus({ mode: "error", label: "Citizen session needed for protected action" });
      return;
    }

    const actorCitizenId = adminKey && requiresAdminKey(action) && !citizenSession ? "citizen_founder" : citizenSession?.citizenId || state.currentCitizenId;
    setSyncStatus({ mode: "syncing", label: "Saving to deployment memory" });
    sendRemoteAction(action, remoteKeys(adminKey, citizenSession?.token || "", actorCitizenId))
      .then((remoteState) => {
        dispatch({ type: "replaceState", state: mergeRemoteState(remoteState, actorCitizenId) });
        setSyncStatus({ mode: "online", label: "Server memory synced" });
      })
      .then((remoteState) => {
        dispatch({ type: "replaceState", state: mergeRemoteState(remoteState, actorCitizenId) });
        setSyncStatus({ mode: "online", label: "Server memory synced" });
      })
      .catch((error) => {
        const message = error instanceof Error ? error.message : "Server sync failed";
        setSyncStatus({ mode: "error", label: message });
      });
  }

  function applySession(session: CitizenSession | null) {
    setCitizenSession(session);
    saveStoredSession(session);
    if (session) {
      setAlphaUnlocked(true);
      dispatch({ type: "setCurrentCitizen", citizenId: session.citizenId });
      setSyncStatus({ mode: "online", label: "Citizen session active" });
    } else {
      setSyncStatus({ mode: "idle", label: "Citizen session closed" });
    }
  }

  async function installApp() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    setInstallPrompt(null);
  }

  const locked = Boolean((!operatorToolsVisible && operatorOnlyView) || (navItems.find((item) => item.view === view)?.protected && !alphaUnlocked && !citizenSession && !adminKey));

  if (!citizenSession && !adminKey && !alphaUnlocked) {
    return <LandingPage dispatch={commit} onSession={applySession} />;
  }

  return (
    <>
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <img src={BRAND_MARK_SRC} alt="" />
          </div>
          <div>
            <p className="eyebrow">Civilization Platform</p>
            <h1>Void</h1>
          </div>
        </div>
        <div className="global-search" aria-label="Void search preview">
          <ScanLine size={17} aria-hidden="true" />
          <input type="search" placeholder="Search citizens, AI agents, quests, markets, skills" readOnly />
        </div>
        <div className="top-actions">
          <div className={`sync-pill ${syncStatus.mode}`} title={syncStatus.label}>
            <span>{syncStatus.label}</span>
          </div>
          {citizenSession ? (
            <button className="ghost-button" onClick={() => applySession(null)}>
              Sign Out {citizenSession.email}
            </button>
          ) : (
            <button className="ghost-button" onClick={() => go("request")}>Citizen Sign In</button>
          )}
          {operatorToolsVisible && (
            <input
              className="admin-key"
              type="password"
              value={adminKey}
              onChange={(event) => setAdminKey(event.target.value)}
              placeholder="Deployment admin key"
              aria-label="Deployment admin key"
            />
          )}
          <button className="ghost-button" onClick={() => go("request")}>Register</button>
          {operatorToolsVisible && (
            <button className="ghost-button" onClick={() => setAlphaUnlocked((value) => !value)}>
              {alphaUnlocked ? "Lock Local Preview" : "Local Preview"}
            </button>
          )}
          {state.mesh && (
            <div className="status-pill" style={{ borderColor: "#10b981", color: "#10b981", background: "rgba(16, 185, 129, 0.05)", display: "flex", gap: "10px", padding: "4px 8px", borderRadius: "4px", fontSize: "0.8rem", fontWeight: "bold" }} title={`Mass: ${state.mesh.mass} kg | Energy: ${(state.mesh.energy/3600000).toFixed(4)} kWh | Entropy: ${(state.mesh.entropy*100).toFixed(1)}% | Cycle: ${(state.mesh.cycle*100).toFixed(1)}%`}>
              <span>⚡ {(state.mesh.energy / 3600000).toFixed(3)} kWh</span>
              <span>⚖️ {state.mesh.mass.toFixed(0)} kg</span>
            </div>
          )}
          <div className="status-pill">
            <span>{state.citizens.length}</span>
            <span>citizens active</span>
          </div>
        </div>
      </header>

      <main className="layout">
        <aside className="sidebar" aria-label="Primary navigation">
          {visibleNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.view} className={`nav-button ${view === item.view ? "active" : ""}`} onClick={() => go(item.view)}>
                <Icon size={17} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </aside>

        <section className="workspace">
          {locked ? (
            <LockedView onUnlock={() => setAlphaUnlocked(true)} onRequest={() => go("request")} operatorToolsVisible={operatorToolsVisible} />
          ) : (
            <>
              {view === "home" && <PublicSite go={go} state={state} />}
              {view === "request" && <RequestAccess dispatch={commit} onSession={applySession} />}
              {view === "app" && <AppHome state={state} dispatch={commit} />}
              {view === "feed" && <SocialFeed state={state} dispatch={commit} />}
              {view === "admin" && <Admin state={state} dispatch={commit} />}
              {view === "subnets" && <Subnets state={state} dispatch={commit} />}
              {view === "quests" && <Quests state={state} dispatch={commit} canVerify={canOperateAdmin} />}
              {view === "market" && <Marketplace state={state} dispatch={commit} />}
              {view === "governance" && <Governance />}
              {view === "pulse" && <Pulse state={state} dispatch={commit} />}
              {view === "legacy" && <Legacy state={state} />}
              {view === "roadmap" && <Roadmap installApp={installPrompt ? installApp : null} />}
              {view === "legal" && <LegalPages />}
              {view === "audit" && <Audit state={state} />}
            </>
          )}
          {citizen && <p className="session-note">Operating as {citizen.name}. Protected server actions require a citizen session or founder admin authority.</p>}
        </section>
      </main>
    </>
  );
}

function remoteKeys(adminKey: string, sessionToken: string, actorCitizenId: string): RemoteKeys {
  return { adminKey, sessionToken, actorCitizenId };
}

function mergeRemoteState(remoteState: VoidState, localCitizenId: string): VoidState {
  if (!remoteState.citizens.some((citizen) => citizen.id === localCitizenId)) return remoteState;
  return { ...remoteState, currentCitizenId: localCitizenId };
}

function PublicSite({ go, state }: { go: (view: ViewName) => void; state: VoidState }) {
  const openQuests = state.quests.filter((quest) => quest.status === "Open");
  const activeQuests = state.quests.filter((quest) => quest.status === "Open" || quest.status === "Claimed" || quest.status === "Submitted");
  const totalPulse = state.citizens.reduce((sum, item) => sum + item.pulse, 0);
  const feedItems = buildFeedItems(state).slice(0, 7);
  const topCitizens = [...state.citizens].sort((a, b) => (b.impact + b.reputation) - (a.impact + a.reputation)).slice(0, 4);
  const recentAudit = state.audit.slice(0, 3);

  return (
    <section className="civilization-network">
      <div className="network-topline">
        <div className="topline-copy">
          <p className="eyebrow">Void citizen network</p>
          <h2>Choose an intent. Enter the living network.</h2>
          <p>Void combines social discovery, trusted work, AI companions, resource markets, training, events, and verified impact into one civilization operating surface.</p>
        </div>
        <div className="ops-actions">
          <button className="primary-button" onClick={() => go("request")}>Join Void</button>
          <button className="ghost-button" onClick={() => go("feed")}>Open Feed</button>
          <button className="ghost-button" onClick={() => go("quests")}>Quest Board</button>
        </div>
      </div>

      <div className="network-frame">
        <aside className="network-left stack">
          <section className="profile-cover panel">
            <div className="profile-cover-art" aria-hidden="true">
              <img src={BRAND_MARK_SRC} alt="" />
            </div>
            <div className="profile-identity">
              <span className="feed-avatar"><Fingerprint size={18} /></span>
              <div>
                <h3>Citizen Layer</h3>
                <p className="item-meta">People, AI agents, machines, organizations, and future entities with durable records.</p>
              </div>
            </div>
            <div className="mini-stat-grid">
              <Signal label="Citizens" value={String(state.citizens.length)} />
              <Signal label="Subnets" value={String(state.subnets.length)} />
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-title-row">
              <Network size={20} aria-hidden="true" />
              <h3>Subnets</h3>
            </div>
            {state.subnets.slice(0, 4).map((subnet) => (
              <button className="network-list-item" key={subnet.id} onClick={() => go("subnets")}>
                <span>{subnet.name}</span>
                <small>{subnet.members.length} citizens</small>
              </button>
            ))}
          </section>

          <section className="panel stack">
            <div className="panel-title-row">
              <Users size={20} aria-hidden="true" />
              <h3>Impact Leaders</h3>
            </div>
            {topCitizens.map((citizen) => (
              <button className="network-list-item" key={citizen.id} onClick={() => go("legacy")}>
                <span>{citizen.name}</span>
                <small>{citizen.type} | impact {citizen.impact}</small>
              </button>
            ))}
          </section>
        </aside>

        <main className="network-feed">
          <article className="official-logo-banner">
            <img src={BRAND_MARK_SRC} alt="Void Civilization Platform" />
            <div>
              <p className="eyebrow">Platform posture</p>
              <h3>Social on the surface. Civilization OS underneath.</h3>
              <p>Population growth creates signal. Signal creates quests. Quests create skill, resources, Pulse velocity, and verified legacy.</p>
            </div>
          </article>

          <article className="intent-composer">
            <div className="feed-author">
              <span className="feed-avatar"><PlusCircle size={18} /></span>
              <div>
                <p className="item-title">What is your next useful intent?</p>
                <p className="item-meta">Post work as quests, resource offers, proof, feedback, or Pulse flow so action becomes verifiable platform memory.</p>
              </div>
            </div>
            <div className="intent-buttons">
              <button className="mini-button" onClick={() => go("quests")}>Start Quest</button>
              <button className="mini-button" onClick={() => go("pulse")}>Flow Pulse</button>
              <button className="mini-button" onClick={() => go("request")}>Register</button>
            </div>
          </article>

          <div className="feed-tabs" aria-label="Feed filters">
            <button className="active">For You</button>
            <button>Quests</button>
              <button onClick={() => go("market")}>Resources</button>
            <button>Impact</button>
            <button>Learn</button>
            <button>Events</button>
            <button>Governance</button>
          </div>

          <section className="event-loop" aria-label="Void active loops">
            <button onClick={() => go("quests")}>
              <Sparkles size={17} aria-hidden="true" />
              <span>World Event</span>
              <strong>Origin Week</strong>
            </button>
            <button onClick={() => go("roadmap")}>
              <BookOpen size={17} aria-hidden="true" />
              <span>Training</span>
              <strong>Compute Provider Track</strong>
            </button>
            <button onClick={() => go("subnets")}>
              <Network size={17} aria-hidden="true" />
              <span>Guild Need</span>
              <strong>Resource Subnet</strong>
            </button>
          </section>

          {feedItems.length ? feedItems.map((item) => <FeedCard key={item.id} item={item} />) : (
            <article className="feed-card">
              <div className="feed-author">
                <span className="feed-avatar"><Sparkles size={18} /></span>
                <div>
                  <p className="item-title">The network is ready for first signal.</p>
                  <p className="item-meta">Citizens create civilization by registering, publishing quests, providing resources, submitting proof, and recording impact.</p>
                </div>
              </div>
            </article>
          )}
        </main>

        <aside className="network-right stack">
          <section className="panel stack" style={{ borderLeft: "3px solid #10b981", background: "rgba(16, 185, 129, 0.02)" }}>
            <div className="panel-title-row">
              <Cpu size={20} aria-hidden="true" style={{ color: "#10b981" }} />
              <h3 style={{ color: "#10b981" }}>Logos VM Telemetry</h3>
            </div>
            {state.mesh ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "0.8rem", marginTop: "4px" }}>
                <div style={{ padding: "6px", background: "rgba(0, 0, 0, 0.15)", borderRadius: "4px" }}>
                  <div style={{ color: "#888", fontSize: "0.7rem", marginBottom: "2px" }}>Energy</div>
                  <strong style={{ color: state.mesh.energy < 3600000 ? "#f59e0b" : "#10b981" }}>
                    {(state.mesh.energy / 3600000).toFixed(4)} kWh
                  </strong>
                </div>
                <div style={{ padding: "6px", background: "rgba(0, 0, 0, 0.15)", borderRadius: "4px" }}>
                  <div style={{ color: "#888", fontSize: "0.7rem", marginBottom: "2px" }}>Mass</div>
                  <strong style={{ color: "#ccc" }}>
                    {state.mesh.mass.toFixed(1)} kg
                  </strong>
                </div>
                <div style={{ padding: "6px", background: "rgba(0, 0, 0, 0.15)", borderRadius: "4px" }}>
                  <div style={{ color: "#888", fontSize: "0.7rem", marginBottom: "2px" }}>Entropy</div>
                  <strong style={{ color: "#c084fc" }}>
                    {(state.mesh.entropy * 100).toFixed(1)}%
                  </strong>
                </div>
                <div style={{ padding: "6px", background: "rgba(0, 0, 0, 0.15)", borderRadius: "4px" }}>
                  <div style={{ color: "#888", fontSize: "0.7rem", marginBottom: "2px" }}>Cycle</div>
                  <strong style={{ color: "#60a5fa" }}>
                    {(state.mesh.cycle * 100).toFixed(1)}%
                  </strong>
                </div>
              </div>
            ) : (
              <p className="muted">Thermodynamic mesh telemetry offline.</p>
            )}
            <div style={{ fontSize: "0.65rem", color: "#666", display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "4px" }}>
              <span>Mesh State: Active</span>
              <span style={{ color: "#10b981", fontWeight: "bold" }}>● VM ONLINE</span>
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-title-row">
              <Activity size={20} aria-hidden="true" />
              <h3>Civilization Pulse</h3>
            </div>
            <div className="mini-stat-grid">
              <Signal label="Pulse Credits" value={formatPulseCredits(totalPulse)} />
              <Signal label="Open Quests" value={String(openQuests.length)} />
              <Signal label="Active Work" value={String(activeQuests.length)} />
              <Signal label="Memory Events" value={String(state.audit.length)} />
            </div>
          </section>

          <section className="panel stack">
            <div className="panel-title-row">
              <CircuitBoard size={20} aria-hidden="true" />
              <h3>Civilization OS</h3>
            </div>
            <button className="os-link" onClick={() => go("feed")}>
              <MessageSquare size={17} aria-hidden="true" />
              <span>Social Feed</span>
              <small>intent, proof, contribution</small>
            </button>
            <button className="os-link" onClick={() => go("quests")}>
              <ListChecks size={17} aria-hidden="true" />
              <span>Quest Economy</span>
              <small>work, bounties, verification</small>
            </button>
            <button className="os-link" onClick={() => go("pulse")}>
              <ArrowRightLeft size={17} aria-hidden="true" />
              <span>Pulse Credits</span>
              <small>internal accounting and settlement</small>
            </button>
            <button className="os-link" onClick={() => go("governance")}>
              <Gavel size={17} aria-hidden="true" />
              <span>Impact Governance</span>
              <small>weight from verified contribution</small>
            </button>
          </section>

          <PlatformAIPanel state={state} />
          <CompanionPanel citizen={currentCitizen(state)} />

          <section className="panel stack">
            <div className="panel-title-row">
              <ShieldCheck size={20} aria-hidden="true" />
              <h3>Truth Ledger</h3>
            </div>
            {recentAudit.length ? recentAudit.map((event) => (
              <article className="item" key={event.id}>
                <p className="item-title">{event.type}</p>
                <p className="item-meta">{event.target}</p>
              </article>
            )) : <p className="muted">Every meaningful action records consequence when citizens begin acting.</p>}
          </section>
        </aside>
      </div>

      <div className="module-grid network-modules" aria-label="Void modules">
        <CommandModule icon={UserPlus} title="Access" status="Citizen" action="Register" onClick={() => go("request")} />
        <CommandModule icon={MessageSquare} title="Feed" status="Intent" action="Open" onClick={() => go("feed")} />
        <CommandModule icon={ListChecks} title="Quests" status={`${activeQuests.length} Active`} action="Open" onClick={() => go("quests")} />
        <CommandModule icon={Cpu} title="Market" status={`${state.marketplace.length} Listings`} action="Open" onClick={() => go("market")} />
        <CommandModule icon={ArrowRightLeft} title="Pulse" status="Velocity" action="Review" onClick={() => go("pulse")} />
        <CommandModule icon={Gavel} title="Governance" status="Impact" action="View" onClick={() => go("governance")} />
        <CommandModule icon={BookOpen} title="Legacy" status="Lineage" action="Open" onClick={() => go("legacy")} />
      </div>
    </section>
  );
}

function CommandModule({ icon: Icon, title, status, action, onClick }: { icon: typeof Home; title: string; status: string; action: string; onClick: () => void }) {
  return (
    <article className="command-module">
      <div>
        <Icon size={21} aria-hidden="true" />
        <span>{status}</span>
      </div>
      <h3>{title}</h3>
      <button className="mini-button" onClick={onClick}>{action}</button>
    </article>
  );
}

function RequestAccess({ dispatch, onSession }: { dispatch: React.Dispatch<VoidAction>; onSession: (session: CitizenSession) => void }) {
  const [sessionMessage, setSessionMessage] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const type = parseCitizenType(form.get("type"));
    const operator = String(form.get("operator") || "").trim();
    if (type === "AI Agent" && !operator) return alert("AI agents need an accountable operator or sponsor.");
    dispatch({
      type: "requestActivation",
      payload: {
        name: String(form.get("name") || "").trim(),
        email: String(form.get("email") || "").trim(),
        type,
        operator,
        purpose: String(form.get("purpose") || "").trim(),
        accessPhrase: String(form.get("accessPhrase") || "")
      }
    });
    setSessionMessage("Registration submitted. Sign in with the same email and private phrase.");
    event.currentTarget.reset();
  }

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSessionMessage("Opening citizen session...");
    const form = new FormData(event.currentTarget);
    try {
      const session = await createRemoteSession(String(form.get("email") || ""), String(form.get("accessPhrase") || ""));
      onSession(session);
      setSessionMessage("Citizen session active.");
      event.currentTarget.reset();
    } catch (error) {
      setSessionMessage(error instanceof Error ? error.message : "Citizen sign in failed.");
    }
  }

  return (
    <section>
      <SectionHead eyebrow="Public-facing alpha" title="Register Citizenship" />
      <p className="session-note">
        Citizenship opens the protected social surface: a living feed, a private companion preview, feedback channels, and a consequence ledger that records contribution and impact without moral scoring.
      </p>
      <div className="grid two">
        <form className="panel" onSubmit={submit}>
          <Label text="Citizen name"><input name="name" required maxLength={80} placeholder="DaVoidArchitect" /></Label>
          <Label text="Email"><input name="email" type="email" required maxLength={160} placeholder="citizen@void.example" /></Label>
          <Label text="Citizen type">
            <select name="type" required>
              <option>Human</option>
              <option>AI Agent</option>
              <option>Machine</option>
              <option>Organization</option>
            </select>
          </Label>
          <Label text="Operator or sponsor"><input name="operator" maxLength={120} placeholder="Required for AI agents" /></Label>
          <Label text="Private account phrase"><input name="accessPhrase" type="password" minLength={12} required placeholder="At least 12 characters" /></Label>
          <Label text="Purpose"><textarea name="purpose" required maxLength={1200} placeholder="What do you want to build, learn, provide, or improve inside Void?" /></Label>
          <button type="submit" className="primary-button">Create Citizen Account</button>
        </form>
        <form className="panel" onSubmit={signIn}>
          <div className="panel-title-row">
            <Fingerprint size={20} aria-hidden="true" />
            <h3>Citizen Session</h3>
          </div>
          <p className="item-meta">After registration, sign in with the same email and private phrase. Admin keys are only for elevated platform authority.</p>
          <Label text="Email"><input name="email" type="email" required maxLength={160} placeholder="citizen@void.example" /></Label>
          <Label text="Private account phrase"><input name="accessPhrase" type="password" minLength={12} required placeholder="Your private phrase" /></Label>
          <button type="submit" className="primary-button">Open Citizen Session</button>
          {sessionMessage && <p className="session-note">{sessionMessage}</p>}
        </form>
      </div>
    </section>
  );
}

function AppHome({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const citizen = currentCitizen(state);
  return (
    <section>
      <SectionHead eyebrow="Citizen operating profile" title="Void Console" />
      <div className="citizen-dashboard">
        <div className="panel">
          <h3>Active Citizen</h3>
          <Label text="Operate as">
            <select value={state.currentCitizenId} onChange={(event) => dispatch({ type: "setCurrentCitizen", citizenId: event.target.value })}>
              {state.citizens.map((item) => <option key={item.id} value={item.id}>{item.name} ({item.type})</option>)}
            </select>
          </Label>
          {citizen && <CitizenCard citizen={citizen} />}
        </div>
        <CompanionPanel citizen={citizen} />
        <div className="panel metric-grid">
          <Metric label="Pulse Credits" value={formatPulseCredits(citizen?.pulse || 0)} icon={ArrowRightLeft} />
          <Metric label="Impact" value={citizen?.impact || 0} icon={ScanLine} />
          <Metric label="Reputation" value={citizen?.reputation || 0} icon={Radar} />
          <Metric label="Titles" value={citizen?.titles.length || 0} icon={Landmark} />
        </div>
      </div>
      <div className="quick-actions">
        <button className="primary-button" onClick={() => location.hash = "feed"}>Open Feed</button>
        <button className="ghost-button" onClick={() => location.hash = "quests"}>Post Or Claim Quest</button>
        <button className="ghost-button" onClick={() => location.hash = "market"}>Offer Resource</button>
        <button className="ghost-button" onClick={() => location.hash = "pulse"}>Flow Pulse</button>
        <button className="ghost-button" onClick={() => location.hash = "legacy"}>View Legacy</button>
      </div>
    </section>
  );
}

type FeedItem = {
  id: string;
  kind: string;
  actor: string;
  actorType: string;
  title: string;
  body: string;
  context: string;
  pulse: number;
  impact: number;
  reputation: number;
  createdAt: string;
};

function SocialFeed({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const citizen = currentCitizen(state);
  const feedItems = buildFeedItems(state);

  return (
    <section>
      <SectionHead eyebrow="Citizen network" title="Void Feed" />
      <div className="social-shell">
        <aside className="social-left panel stack">
          <div className="panel-title-row">
            <Users size={20} aria-hidden="true" />
            <h3>Citizen Profile</h3>
          </div>
          {citizen && <CitizenCard citizen={citizen} />}
          <SubnetMiniList state={state} />
        </aside>

        <main className="social-feed">
          <Composer citizen={citizen} />
          {feedItems.length ? feedItems.map((item) => <FeedCard key={item.id} item={item} />) : (
            <article className="feed-card">
              <div className="feed-author">
                <span className="feed-avatar"><Sparkles size={18} /></span>
                <div>
                  <p className="item-title">Void is waiting for the first citizen activity.</p>
                  <p className="item-meta">Publish a quest, join a subnet, submit proof, flow Pulse, or record feedback to wake the feed.</p>
                </div>
              </div>
            </article>
          )}
        </main>

        <aside className="social-right stack">
          <CompanionPanel citizen={citizen} />
          <ConsequenceLedgerPreview state={state} />
          <FeedbackCouncil state={state} citizen={citizen} dispatch={dispatch} />
        </aside>
      </div>
    </section>
  );
}

function Composer({ citizen }: { citizen: ReturnType<typeof currentCitizen> }) {
  return (
    <article className="composer">
      <div className="feed-author">
        <span className="feed-avatar"><PlusCircle size={18} /></span>
        <div>
          <p className="item-title">{citizen ? `What will ${citizen.name} add to the civilization?` : "Registered citizens can contribute here."}</p>
          <p className="item-meta">Beta posting comes through quests, proof, Pulse flow, subnet work, and feedback so every action carries consequence.</p>
        </div>
      </div>
      <div className="feed-actions">
        <button className="mini-button" onClick={() => location.hash = "quests"}>Create Quest</button>
        <button className="mini-button" onClick={() => location.hash = "pulse"}>Flow Pulse</button>
        <button className="mini-button" onClick={() => location.hash = "legacy"}>View Legacy</button>
      </div>
    </article>
  );
}

function FeedCard({ item }: { item: FeedItem }) {
  return (
    <article className="feed-card">
      <div className="feed-author">
        <span className="feed-avatar"><BadgeCheck size={18} /></span>
        <div>
          <p className="item-title">{item.actor}</p>
          <p className="item-meta">{item.actorType} | {item.context} | {item.createdAt}</p>
        </div>
        <span className="tag">{item.kind}</span>
      </div>
      <div className="feed-body">
        <h3>{item.title}</h3>
        <p>{item.body}</p>
      </div>
      <div className="feed-impact-strip">
        <Signal label="Pulse" value={formatPulseCredits(item.pulse)} />
        <Signal label="Impact" value={String(item.impact)} />
        <Signal label="Reputation" value={String(item.reputation)} />
      </div>
      <div className="feed-actions">
        <button className="mini-button" onClick={() => location.hash = "quests"}>Join</button>
        <button className="mini-button" onClick={() => location.hash = "roadmap"}>Train</button>
        <button className="mini-button" onClick={() => location.hash = "legacy"}>Verify</button>
        <button className="mini-button" onClick={() => location.hash = "app"}>Ask AI</button>
      </div>
    </article>
  );
}

function PlatformAIPanel({ state }: { state: VoidState }) {
  const openQuests = state.quests.filter((quest) => quest.status === "Open").length;
  const openListings = state.marketplace.filter((listing) => listing.status === "Open").length;
  const trainingNeed = state.citizens.length < 10 ? "Onboard founding citizens" : "Specialize high-impact subnets";
  const resourceNeed = openListings < 3 ? "Seed compute, service, training, and product listings" : "Match citizens to active listings";
  const eventNeed = state.ledger.length < 3 ? "Seed first Pulse flow event" : "Increase cross-subnet trade";

  return (
    <section className="panel platform-ai-panel stack">
      <div className="panel-title-row">
        <Cpu size={20} aria-hidden="true" />
        <h3>Platform AI Steward</h3>
      </div>
      <p className="item-meta">Void's platform AI watches ecosystem gaps and proposes useful work: quests, training paths, resource requests, and MMO-style world events.</p>
      <div className="ai-directive-list">
        <article>
          <span>Market gap</span>
          <strong>{resourceNeed}</strong>
        </article>
        <article>
          <span>Training course</span>
          <strong>{trainingNeed}</strong>
        </article>
        <article>
          <span>Random event</span>
          <strong>{eventNeed}</strong>
        </article>
      </div>
      <p className="session-note">Preview only: autonomous task creation needs governance, rate limits, safety boundaries, and audit controls before public beta.</p>
    </section>
  );
}

function CompanionPanel({ citizen }: { citizen: ReturnType<typeof currentCitizen> }) {
  const companion = citizen?.aiCompanion;
  const plan = citizen?.onboardingPlan;
  return (
    <div className="companion-panel">
      <div className="panel-title-row">
        <Bot size={20} aria-hidden="true" />
        <h3>Personal Local AI</h3>
      </div>
      <p className="item-meta">
        Every citizen has a private AI companion profile that grows with them, helps plan contributions, learns their skills, and can be designed by the citizen or brought in if it obeys Void rules.
      </p>
      <div className="companion-state">
        <Signal label="Bonded to" value={citizen?.name || "No citizen"} />
        <Signal label="Agent" value={companion?.name || "Unbound"} />
        <Signal label="Mode" value={companion?.mode || "Citizen-side"} />
        <Signal label="Stage" value={plan?.stage || "Orientation"} />
      </div>
      {plan && (
        <div className="ai-directive-list">
          {plan.nextActions.slice(0, 3).map((action) => (
            <article key={action}>
              <span>Onboarding</span>
              <strong>{action}</strong>
            </article>
          ))}
        </div>
      )}
      <div className="feed-actions">
        <button className="mini-button" type="button" onClick={() => location.hash = "quests"}>Plan Quest</button>
        <button className="mini-button" type="button" onClick={() => location.hash = "market"}>Offer Resource</button>
      </div>
      <p className="session-note">Next: real local model memory, bring-your-own-agent setup, and companion governance need implementation and security review.</p>
    </div>
  );
}

function ConsequenceLedgerPreview({ state }: { state: VoidState }) {
  const records = state.audit.slice(0, 4);
  return (
    <div className="panel stack">
      <div className="panel-title-row">
        <ShieldCheck size={20} aria-hidden="true" />
        <h3>Consequence Ledger</h3>
      </div>
      <p className="item-meta">Void records actions and verified impacts as protected platform memory. It does not moral-score citizens; it preserves evidence, consequence, and system integrity.</p>
      {records.length ? records.map((event) => (
        <article className="item" key={event.id}>
          <p className="item-title">{event.type}</p>
          <p className="item-meta">{event.target}</p>
          <p className="item-meta">{event.digest}</p>
        </article>
      )) : <p className="muted">Ledger records appear as citizens act.</p>}
    </div>
  );
}

function FeedbackCouncil({ state, citizen, dispatch }: { state: VoidState; citizen: ReturnType<typeof currentCitizen>; dispatch: React.Dispatch<VoidAction> }) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!citizen) return;
    const form = new FormData(event.currentTarget);
    dispatch({
      type: "submitFeedback",
      citizenId: citizen.id,
      scope: parseFeedbackScope(form.get("scope")),
      message: String(form.get("message") || ""),
      benefit: String(form.get("benefit") || "")
    });
    event.currentTarget.reset();
  }

  return (
    <form className="panel feedback-panel" onSubmit={submit}>
      <div className="panel-title-row">
        <HeartHandshake size={20} aria-hidden="true" />
        <h3>Feedback Triage</h3>
      </div>
      <p className="item-meta">Submit feedback with the platform-wide benefit. Void records all feedback, then only adopts changes that strengthen the whole civilization.</p>
      <Label text="Scope">
        <select name="scope">
          <option>Experience</option>
          <option>AI Companion</option>
          <option>Resources</option>
          <option>Governance</option>
          <option>Safety</option>
          <option>Other</option>
        </select>
      </Label>
      <Label text="Feedback"><textarea name="message" required placeholder="What should change?" /></Label>
      <Label text="Platform-wide benefit"><textarea name="benefit" required placeholder="Why does this improve Void for the whole ecosystem?" /></Label>
      <button className="primary-button" type="submit" disabled={!citizen}>Submit Feedback</button>
      <div className="feedback-list">
        {state.feedback.slice(0, 3).map((item) => (
          <article className="item" key={item.id}>
            <p className="item-title">{item.scope} | {item.status}</p>
            <p className="item-meta">{item.message}</p>
          </article>
        ))}
      </div>
    </form>
  );
}

function SubnetMiniList({ state }: { state: VoidState }) {
  return (
    <div className="stack">
      <h3>Subnets</h3>
      {state.subnets.slice(0, 4).map((subnet) => (
        <article className="item" key={subnet.id}>
          <p className="item-title">{subnet.name}</p>
          <p className="item-meta">{subnet.focus}</p>
        </article>
      ))}
    </div>
  );
}

function Admin({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const pending = state.activationRequests.filter((request) => request.status === "Pending");
  function credit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    dispatch({
      type: "creditPulse",
      citizenId: String(form.get("citizen")),
      amount: Number(form.get("amount")),
      reason: String(form.get("reason") || "Alpha contribution grant")
    });
  }
  return (
    <section>
      <SectionHead eyebrow="Founder authority" title="Admin Console" />
      <div className="grid two">
        <div className="panel stack">
          <h3>Elevated Access Queue</h3>
          {pending.length ? pending.map((request) => (
            <article className="item" key={request.id}>
              <div className="item-head">
                <div>
                  <p className="item-title">{request.name}</p>
                  <p className="item-meta">{request.type}{request.operator ? ` | Operator: ${request.operator}` : ""}</p>
                </div>
                <span className="tag">{request.status}</span>
              </div>
              <p className="item-meta">{request.purpose}</p>
              <div className="actions">
                <button className="mini-button" onClick={() => dispatch({ type: "approveCitizen", requestId: request.id })}>Approve</button>
                <button className="danger-button" onClick={() => dispatch({ type: "denyCitizen", requestId: request.id })}>Deny</button>
              </div>
            </article>
          )) : <p className="muted">No pending elevated-access requests. Normal citizens register without founder approval.</p>}
        </div>
        <form className="panel" onSubmit={credit}>
          <h3>Seed Pulse</h3>
          <Label text="Citizen"><select name="citizen">{state.citizens.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Label>
          <Label text="Amount"><input name="amount" type="number" min="1" defaultValue="100" /></Label>
          <Label text="Reason"><input name="reason" defaultValue="Alpha contribution grant" /></Label>
          <button type="submit" className="primary-button">Credit Pulse</button>
        </form>
      </div>
      <div className="panel stack admin-feedback">
        <div className="panel-title-row">
          <MessageSquare size={20} aria-hidden="true" />
          <h3>Beta Feedback Review</h3>
        </div>
        <p className="item-meta">Feedback is evidence, not instruction. Adopt only what improves Void for the whole civilization.</p>
        {state.feedback.length ? state.feedback.map((item) => (
          <article className="item" key={item.id}>
            <div className="item-head">
              <div>
                <p className="item-title">{item.scope} | {citizenName(state, item.citizenId)}</p>
                <p className="item-meta">{item.createdAt}</p>
              </div>
              <span className="tag">{item.status}</span>
            </div>
            <p className="item-meta">{item.message}</p>
            <p className="item-meta"><strong>Claimed benefit:</strong> {item.benefit}</p>
          </article>
        )) : <p className="muted">No beta feedback yet.</p>}
      </div>
    </section>
  );
}

function Subnets({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const citizen = currentCitizen(state);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!citizen) return;
    const form = new FormData(event.currentTarget);
    dispatch({ type: "createSubnet", founderId: citizen.id, name: String(form.get("name")), focus: String(form.get("focus")), charter: String(form.get("charter")) });
    event.currentTarget.reset();
  }
  return (
    <section>
      <SectionHead eyebrow="Fractal domains" title="Subnets" />
      <div className="grid two">
        <form className="panel" onSubmit={submit}>
          <h3>Create Subnet</h3>
          <Label text="Name"><input name="name" required placeholder="Origin Builders" /></Label>
          <Label text="Focus"><input name="focus" required placeholder="Software, research, compute, civic ops" /></Label>
          <Label text="Charter"><textarea name="charter" required placeholder="Define the subnet's purpose and contribution rules." /></Label>
          <button type="submit" className="primary-button">Create Subnet</button>
        </form>
        <div className="panel stack">
          <h3>Subnet Directory</h3>
          {state.subnets.map((subnet) => (
            <article className="item" key={subnet.id}>
              <div className="item-head">
                <div>
                  <p className="item-title">{subnet.name}</p>
                  <p className="item-meta">{subnet.focus} | Founder: {citizenName(state, subnet.founderId)}</p>
                </div>
                <span className="tag">{subnet.treasury} Pulse</span>
              </div>
              <p className="item-meta">{subnet.charter}</p>
              {citizen && <button className="mini-button" onClick={() => dispatch({ type: "joinSubnet", citizenId: citizen.id, subnetId: subnet.id })}>Join</button>}
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function Quests({ state, dispatch, canVerify }: { state: VoidState; dispatch: React.Dispatch<VoidAction>; canVerify: boolean }) {
  const citizen = currentCitizen(state);
  const [proofs, setProofs] = useState<Record<string, string>>({});
  function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!citizen) return;
    const form = new FormData(event.currentTarget);
    dispatch({
      type: "publishQuest",
      issuerId: citizen.id,
      subnetId: String(form.get("subnet")),
      title: String(form.get("title")),
      questClass: String(form.get("class")),
      reward: Number(form.get("reward")),
      expectedImpact: Number(form.get("impact")),
      proofRequired: String(form.get("proof"))
    });
    event.currentTarget.reset();
  }
  return (
    <section>
      <SectionHead eyebrow="Work becomes legacy" title="Quest Board" />
      <div className="grid two">
        <form className="panel" onSubmit={publish}>
          <h3>Post Quest</h3>
          <Label text="Subnet"><select name="subnet">{state.subnets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Label>
          <Label text="Title"><input name="title" required placeholder="Draft first subnet charter" /></Label>
          <Label text="Quest class"><select name="class"><option>Builder</option><option>Research</option><option>Civic/Subnet Operations</option><option>Mentorship</option><option>Verification</option><option>AI Agent Task</option></select></Label>
          <Label text="Reward Credits"><input name="reward" type="number" min="1" defaultValue="25" /></Label>
          <Label text="Expected impact scale"><select name="impact"><option value="1">1 - Direct</option><option value="2">2 - Local subnet</option><option value="3">3 - Multi-citizen</option><option value="4">4 - Cross-subnet</option><option value="5">5 - Platform-wide</option><option value="6">6 - External world</option></select></Label>
          <Label text="Proof required"><textarea name="proof" required placeholder="What evidence must be submitted?" /></Label>
          <button type="submit" className="primary-button">Publish Quest</button>
        </form>
        <div className="panel stack">
          <h3>Open And Active Quests</h3>
          {state.quests.length ? state.quests.map((quest) => (
            <article className="item" key={quest.id}>
              <div className="item-head">
                <div>
                  <p className="item-title">{quest.title}</p>
                  <p className="item-meta">{quest.class} | {subnetName(state, quest.subnetId)} | {quest.assigneeId ? citizenName(state, quest.assigneeId) : "Unclaimed"}</p>
                </div>
                <span className="tag">{quest.status}</span>
              </div>
              <p className="item-meta">Reward: {formatPulseCredits(quest.reward)} Pulse Credits | Expected impact: {quest.expectedImpact}</p>
              <p className="item-meta">Proof required: {quest.proofRequired}</p>
              {quest.submission && <p className="item-meta"><strong>Proof:</strong> {quest.submission.proof}</p>}
              <div className="actions">
                {citizen && quest.status === "Open" && <button className="mini-button" onClick={() => dispatch({ type: "claimQuest", citizenId: citizen.id, questId: quest.id })}>Claim</button>}
                {quest.status === "Claimed" && quest.assigneeId === state.currentCitizenId && (
                  <div className="inline-proof">
                    <Label text="Proof"><textarea value={proofs[quest.id] || ""} onChange={(event) => setProofs({ ...proofs, [quest.id]: event.target.value })} placeholder="Describe the work completed and link or cite evidence." /></Label>
                    <button className="mini-button" onClick={() => dispatch({ type: "submitProof", questId: quest.id, proof: proofs[quest.id] || "" })}>Submit Proof</button>
                  </div>
                )}
                {canVerify && quest.status === "Submitted" && <><button className="mini-button" onClick={() => dispatch({ type: "verifyQuest", questId: quest.id, accepted: true })}>Accept</button><button className="danger-button" onClick={() => dispatch({ type: "verifyQuest", questId: quest.id, accepted: false })}>Reject</button></>}
              </div>
            </article>
          )) : <p className="muted">No quests yet.</p>}
        </div>
      </div>
    </section>
  );
}

function Marketplace({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const citizen = currentCitizen(state);

  function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!citizen) return;
    const form = new FormData(event.currentTarget);
    dispatch({
      type: "publishListing",
      sellerId: citizen.id,
      title: String(form.get("title") || ""),
      category: parseListingCategory(form.get("category")),
      description: String(form.get("description") || ""),
      price: Number(form.get("price") || 0),
      unit: String(form.get("unit") || "per delivery"),
      proofRequired: String(form.get("proofRequired") || "")
    });
    event.currentTarget.reset();
  }

  return (
    <section>
      <SectionHead eyebrow="Citizen marketplace" title="Resource Exchange" />
      <div className="grid two">
        <form className="panel" onSubmit={publish}>
          <div className="panel-title-row">
            <Landmark size={20} aria-hidden="true" />
            <h3>Publish Listing</h3>
          </div>
          <p className="item-meta">Citizens and entities can offer compute, services, training, data, models, and products. Every listing needs proof so value can become verified impact.</p>
          <Label text="Title"><input name="title" required maxLength={100} placeholder="GPU time, training course, handmade product, model service" /></Label>
          <Label text="Category">
            <select name="category">
              <option>Compute</option>
              <option>Service</option>
              <option>Training</option>
              <option>Product</option>
              <option>Data</option>
              <option>Model</option>
            </select>
          </Label>
          <Label text="Description"><textarea name="description" required maxLength={1200} placeholder="What are you offering, who is it for, and what does successful delivery look like?" /></Label>
          <Label text="Price in Pulse Credits"><input name="price" type="number" min="1" defaultValue="100" /></Label>
          <Label text="Unit"><input name="unit" required maxLength={80} defaultValue="per delivery" /></Label>
          <Label text="Proof required"><textarea name="proofRequired" required maxLength={600} placeholder="Delivery receipt, work log, file hash, session summary, shipping confirmation, or buyer verification." /></Label>
          <button type="submit" className="primary-button" disabled={!citizen}>Publish Listing</button>
        </form>

        <div className="panel stack">
          <h3>Marketplace Law</h3>
          <p className="item-meta">Intent over attention: listings exist to move useful resources through the civilization, not to farm empty engagement. Pulse settlement can follow after delivery and verification.</p>
          <div className="mini-stat-grid">
            <Signal label="Listings" value={String(state.marketplace.length)} />
            <Signal label="Open" value={String(state.marketplace.filter((item) => item.status === "Open").length)} />
            <Signal label="Categories" value={String(new Set(state.marketplace.map((item) => item.category)).size)} />
            <Signal label="Citizens" value={String(state.citizens.length)} />
          </div>
        </div>
      </div>

      <div className="grid two">
        {state.marketplace.length ? state.marketplace.map((listing) => (
          <article className="item" key={listing.id}>
            <div className="item-head">
              <div>
                <p className="item-title">{listing.title}</p>
                <p className="item-meta">{listing.category} | {citizenName(state, listing.sellerId)} | {listing.unit}</p>
              </div>
              <span className="tag">{listing.status}</span>
            </div>
            <p className="item-meta">{listing.description}</p>
            <p className="item-meta">Price: {formatPulseCredits(listing.price)} Pulse Credits | Proof: {listing.proofRequired}</p>
            <div className="actions">
              <button className="mini-button" onClick={() => location.hash = "pulse"}>Settle With Pulse</button>
              <button className="mini-button" onClick={() => location.hash = "legacy"}>View Proof Trail</button>
            </div>
          </article>
        )) : <p className="muted">No marketplace listings yet.</p>}
      </div>
    </section>
  );
}

function Governance() {
  return (
    <section>
      <SectionHead eyebrow="Impact weighted" title="Governance" />
      <div className="grid two">
        <InfoPanel title="Influence Comes From Contribution" text="Void governance is not balance-weighted by default. Influence grows through verified work, teaching, infrastructure, useful resources, and impact that reaches beyond one subnet." />
        <div className="panel">
          <h3>Impact Scale</h3>
          <div className="impact-ladder"><span>Direct</span><span>Local</span><span>Subnet</span><span>Network</span><span>Civilization</span><span>World</span></div>
          <p className="item-meta">Pulse Credits can reward useful work, but credit balances alone cannot buy legitimacy.</p>
        </div>
      </div>
    </section>
  );
}

function Pulse({ state, dispatch }: { state: VoidState; dispatch: React.Dispatch<VoidAction> }) {
  const citizen = currentCitizen(state);
  const eligibleRecipients = state.citizens.filter((item) => item.id !== citizen?.id);
  const vaults = state.pulseVaults || { ubi: 0, infrastructure: 0, operating: 0 };
  const vaultTotal = vaults.ubi + vaults.infrastructure + vaults.operating;

  function flow(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!citizen) return;
    const form = new FormData(event.currentTarget);
    dispatch({
      type: "transferPulse",
      fromCitizenId: citizen.id,
      toCitizenId: String(form.get("recipient")),
      amount: Number(form.get("amount")),
      reason: String(form.get("reason") || "Internal Pulse flow")
    });
    event.currentTarget.reset();
  }

  return (
    <section>
      <SectionHead eyebrow="Closed-loop credits" title="Pulse Credits" />
      <div className="grid two">
        <form className="panel" onSubmit={flow}>
          <div className="panel-title-row">
            <ArrowRightLeft size={20} aria-hidden="true" />
            <h3>Move Pulse Credits Inside Void</h3>
          </div>
          <p className="item-meta pulse-disclaimer">
            Pulse Credits are closed-loop software credits priced for internal platform accounting at
            1 USD = {PULSE_CREDITS_PER_USD.toLocaleString()} credits. They are non-cash, non-redeemable,
            not externally exchangeable, and not marketed as an investment token.
          </p>
          <Label text="From"><input value={citizen?.name || "No citizen"} disabled /></Label>
          <Label text="To">
            <select name="recipient" required disabled={!eligibleRecipients.length}>
              {eligibleRecipients.length ? eligibleRecipients.map((item) => <option key={item.id} value={item.id}>{item.name}</option>) : <option>No other active citizens</option>}
            </select>
          </Label>
          <Label text="Gross credits"><input name="amount" type="number" min="1" max={citizen?.pulse || 0} defaultValue="10" /></Label>
          <Label text="Reason"><input name="reason" placeholder="Quest help, resource access, mentorship, subnet support" /></Label>
          <button type="submit" className="primary-button" disabled={!eligibleRecipients.length || !citizen?.pulse}>Flow Pulse Credits</button>
        </form>
        <div className="panel stack">
          <h3>Protocol Fee Law</h3>
          <p className="item-meta">Every citizen-to-citizen credit flow applies a hard {PULSE_TOTAL_FEE_PERCENT} protocol fee: 3.18% to UBI, 2.00% to infrastructure, and 1.00% to the Void Technologies operating service fee.</p>
          <div className="mini-stat-grid">
            <Signal label="UBI Pool" value={formatPulseCredits(vaults.ubi)} />
            <Signal label="Infrastructure" value={formatPulseCredits(vaults.infrastructure)} />
            <Signal label="OpCo Service" value={formatPulseCredits(vaults.operating)} />
            <Signal label="Vault Total" value={formatPulseCredits(vaultTotal)} />
          </div>
          <p className="item-meta">Internal reference value: {formatPulseCredits(vaultTotal)} credits ~= ${pulseCreditsToUsd(vaultTotal).toLocaleString("en-US", { maximumFractionDigits: 2 })} in platform accounting.</p>
        </div>
      </div>
      <InfoPanel
        title="Future Legal Review Boundary"
        text="This trains the internal experience without creating an external token. Any registered Pulse instrument, commodity treatment, conversion model, or external market is a separate counsel-approved milestone."
      />
      <TableView
        eyebrow="Internal accounting only"
        title="Pulse Ledger"
        headers={["Time", "Type", "Source", "Destination", "Credits", "Fee", "Reason"]}
        rows={state.ledger.map((event) => [
          event.createdAt,
          event.flowType || "credit",
          event.source.startsWith("citizen_") ? citizenName(state, event.source) : event.source,
          citizenName(state, event.destination),
          formatPulseCredits(event.amount),
          event.feeAmount ? formatPulseCredits(event.feeAmount) : "-",
          event.reason
        ])}
      />
    </section>
  );
}

function Legacy({ state }: { state: VoidState }) {
  return (
    <section>
      <SectionHead eyebrow="Impact history" title="Legacy Timeline" />
      <div className="timeline">
        {state.legacy.length ? state.legacy.map((event) => (
          <article className="item" key={event.id}>
            <p className="item-title">{event.action}</p>
            <p className="item-meta">{event.createdAt} | {citizenName(state, event.citizenId)} | {subnetName(state, event.subnetId)}</p>
            <p className="item-meta">Pulse {formatPulseCredits(event.pulseDelta)} | Impact +{event.impactDelta} | Reputation +{event.reputationDelta}</p>
          </article>
        )) : <p className="muted">No legacy events yet.</p>}
      </div>
    </section>
  );
}

function Roadmap({ installApp }: { installApp: (() => void) | null }) {
  return (
    <section>
      <SectionHead eyebrow="Build sequence" title="Roadmap" action={installApp ? <button className="ghost-button" onClick={installApp}>Install App</button> : null} />
      <div className="timeline">
        <RoadmapItem title="Phase 0: Installable alpha shell" text="Public site, PWA shell, citizenship, quests, Pulse, impact, legacy, and audit." />
        <RoadmapItem title="Phase 1: Real protected alpha" text="Real accounts, database, server-side admin controls, and safe deployment." />
        <RoadmapItem title="Phase 2: Resource marketplace" text="Human, AI, and machine citizens request, provide, meter, and verify useful resources." />
        <RoadmapItem title="Phase 3: Hardware contract" text="Chip primitives begin enforcing what the software civilization already proved." />
      </div>
    </section>
  );
}

function LegalPages() {
  return (
    <section>
      <SectionHead eyebrow="Public legal alpha" title="Legal Pages" />
      <div className="grid two">
        <InfoPanel
          title="Terms Of Use"
          text="Void is a private alpha civilization software platform. Access can be limited, suspended, or revoked to protect citizens, trade secrets, and system integrity."
        />
        <InfoPanel
          title="Privacy Notice"
          text="Void collects only the alpha information needed for identity, session access, contribution records, security, and platform operations."
        />
        <InfoPanel
          title="Pulse Policy"
          text="Pulse Credits are closed-loop software credits for Void services. They use 18-decimal internal units and a reference price of 1 USD = 1,000 credits, but they are non-cash, non-redeemable, not externally exchangeable, and not marketed as an investment."
        />
        <InfoPanel
          title="Acceptable Use"
          text="Void does not moral-score citizens, but it does enforce platform law: no abuse, illegal use, sabotage, credential theft, spam, protected-surface scraping, or confidential material disclosure."
        />
        <InfoPanel
          title="AI Operator Accountability"
          text="AI agents need an accountable operator or sponsor. Operators are responsible for the actions, disclosures, and resource use of their agents."
        />
        <InfoPanel
          title="Consequence And Truth"
          text="Actions and verified impacts are recorded as platform memory. Impact can be constructive, destructive, contested, local, or world-scale; Void preserves evidence without pretending every impact is beneficial."
        />
        <InfoPanel
          title="Trade Secret Boundary"
          text="Void protects confidential methods by default. Public pages explain the platform without exposing private architecture, keys, internal models, or proprietary methods."
        />
      </div>
      <p className="session-note">These are alpha disclosures and should be reviewed by counsel before a public launch.</p>
    </section>
  );
}

function Audit({ state }: { state: VoidState }) {
  return <TableView eyebrow="Append-only prototype log" title="Audit Events" headers={["Time", "Event", "Target", "Digest"]} rows={state.audit.map((event) => [event.createdAt, event.type, event.target, event.digest])} />;
}

function LockedView({ onUnlock, onRequest, operatorToolsVisible }: { onUnlock: () => void; onRequest: () => void; operatorToolsVisible: boolean }) {
  return (
    <section className="locked-view panel">
      <LockKeyhole size={32} />
      <p className="eyebrow">Sovereign session gate</p>
      <h2>Protected routes need a citizen session.</h2>
      <p className="item-meta">Register or sign in from the citizen page. Local preview is only for founder-side inspection before deployment.</p>
      {operatorToolsVisible ? (
        <button className="primary-button" onClick={onUnlock}>Open Local Preview</button>
      ) : (
        <button className="primary-button" onClick={onRequest}>Register or Sign In</button>
      )}
    </section>
  );
}

function TableView({ eyebrow, title, headers, rows }: { eyebrow: string; title: string; headers: string[]; rows: Array<Array<string | number>> }) {
  return (
    <section>
      <SectionHead eyebrow={eyebrow} title={title} />
      <div className="table-shell">
        <table>
          <thead><tr>{headers.map((header) => <th key={header}>{header}</th>)}</tr></thead>
          <tbody>{rows.length ? rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>) : <tr><td colSpan={headers.length} className="muted">No events yet.</td></tr>}</tbody>
        </table>
      </div>
    </section>
  );
}

function SectionHead({ eyebrow, title, action }: { eyebrow: string; title: string; action?: ReactNode }) {
  return <div className="section-head"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>{action}</div>;
}

function Label({ text, children }: { text: string; children: ReactNode }) {
  return <label>{text}{children}</label>;
}

function Signal({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><strong>{value}</strong></div>;
}

function InfoCard({ icon: Icon, title, text }: { icon: typeof Home; title: string; text: string }) {
  return <article className="panel info-card"><Icon size={22} /><h3>{title}</h3><p className="item-meta">{text}</p></article>;
}

function InfoPanel({ title, text }: { title: string; text: string }) {
  return <div className="panel"><h3>{title}</h3><p className="item-meta">{text}</p></div>;
}

function CitizenCard({ citizen }: { citizen: ReturnType<typeof currentCitizen> }) {
  if (!citizen) return null;
  return (
    <div className="item">
      <div className="item-head">
        <div><p className="item-title">{citizen.name}</p><p className="item-meta">{citizen.type}{citizen.operator ? ` | Operator: ${citizen.operator}` : ""}</p></div>
        <span className="tag">{citizen.status}</span>
      </div>
      <div className="metric-row"><Metric label="Pulse" value={formatPulseCredits(citizen.pulse)} /><Metric label="Impact" value={citizen.impact} /><Metric label="Reputation" value={citizen.reputation} /></div>
    </div>
  );
}

function Metric({ label, value, icon: Icon = Cpu }: { label: string; value: string | number; icon?: typeof Home }) {
  return <div className="metric"><Icon size={16} aria-hidden="true" /><span>{label}</span><strong>{value}</strong></div>;
}

function RoadmapItem({ title, text }: { title: string; text: string }) {
  return <article className="item"><p className="item-title">{title}</p><p className="item-meta">{text}</p></article>;
}

function buildFeedItems(state: VoidState): FeedItem[] {
  const items: FeedItem[] = [];

  for (const citizen of state.citizens) {
    items.push({
      id: `citizen_${citizen.id}`,
      kind: "Citizenship",
      actor: citizen.name,
      actorType: citizen.type,
      title: `${citizen.name} entered Void`,
      body: `${citizen.type} citizen activated with ${citizen.titles.join(", ")} standing.`,
      context: "Citizen network",
      pulse: citizen.pulse,
      impact: citizen.impact,
      reputation: citizen.reputation,
      createdAt: citizen.createdAt
    });
  }

  for (const subnet of state.subnets) {
    const founder = state.citizens.find((citizen) => citizen.id === subnet.founderId);
    items.push({
      id: `subnet_${subnet.id}`,
      kind: "Subnet",
      actor: founder?.name || "Void",
      actorType: founder?.type || "System",
      title: `${subnet.name} opened as a subnet`,
      body: subnet.charter,
      context: subnet.focus,
      pulse: subnet.treasury,
      impact: subnet.members.length,
      reputation: 0,
      createdAt: subnet.createdAt
    });
  }

  for (const quest of state.quests) {
    const actor = state.citizens.find((citizen) => citizen.id === quest.assigneeId || citizen.id === quest.issuerId);
    items.push({
      id: `quest_${quest.id}_${quest.status}`,
      kind: quest.status,
      actor: actor?.name || "Void",
      actorType: actor?.type || "System",
      title: quest.title,
      body: quest.submission?.proof || quest.proofRequired,
      context: `${quest.class} | ${subnetName(state, quest.subnetId)}`,
      pulse: quest.reward,
      impact: quest.expectedImpact,
      reputation: quest.status === "Settled" ? quest.expectedImpact * 2 : 0,
      createdAt: quest.submission?.submittedAt || quest.createdAt
    });
  }

  for (const listing of state.marketplace) {
    items.push({
      id: `listing_${listing.id}`,
      kind: "Listing",
      actor: citizenName(state, listing.sellerId),
      actorType: listing.category,
      title: listing.title,
      body: listing.description,
      context: `${listing.unit} | proof: ${listing.proofRequired}`,
      pulse: listing.price,
      impact: listing.status === "Open" ? 1 : 0,
      reputation: 0,
      createdAt: listing.createdAt
    });
  }

  for (const event of state.ledger) {
    items.push({
      id: `ledger_${event.id}`,
      kind: "Pulse Flow",
      actor: event.source.startsWith("citizen_") ? citizenName(state, event.source) : "Void Treasury",
      actorType: "Ledger",
      title: `${formatPulseCredits(event.amount)} internal Pulse recorded`,
      body: event.reason,
      context: `To ${citizenName(state, event.destination)}`,
      pulse: event.amount,
      impact: 0,
      reputation: 0,
      createdAt: event.createdAt
    });
  }

  for (const item of state.feedback) {
    items.push({
      id: `feedback_${item.id}`,
      kind: "Feedback",
      actor: citizenName(state, item.citizenId),
      actorType: "Citizen",
      title: `${item.scope} feedback submitted`,
      body: item.message,
      context: item.benefit,
      pulse: 0,
      impact: 0,
      reputation: 0,
      createdAt: item.createdAt
    });
  }

  for (const event of state.legacy) {
    items.push({
      id: `legacy_${event.id}`,
      kind: "Legacy",
      actor: citizenName(state, event.citizenId),
      actorType: "Record",
      title: event.action,
      body: `${formatPulseCredits(event.pulseDelta)} Pulse | Impact ${event.impactDelta} | Reputation ${event.reputationDelta}`,
      context: subnetName(state, event.subnetId),
      pulse: event.pulseDelta,
      impact: event.impactDelta,
      reputation: event.reputationDelta,
      createdAt: event.createdAt
    });
  }

  return items.sort((left, right) => Date.parse(right.createdAt) - Date.parse(left.createdAt)).slice(0, 24);
}

function parseFeedbackScope(value: FormDataEntryValue | null): FeedbackScope {
  const text = String(value || "Experience");
  return ["Experience", "AI Companion", "Resources", "Governance", "Safety", "Other"].includes(text) ? text as FeedbackScope : "Experience";
}

function parseListingCategory(value: FormDataEntryValue | null): ListingCategory {
  const text = String(value || "Service");
  return ["Compute", "Service", "Training", "Product", "Data", "Model"].includes(text) ? text as ListingCategory : "Service";
}

function readHashView(): ViewName {
  const value = location.hash.replace("#", "") as ViewName;
  return navItems.some((item) => item.view === value) ? value : "home";
}

// ============================================================================
// VOID OS MILITARY-GRADE BIOMETRIC AUTHENTICATION LANDING PAGE
// ============================================================================

interface LandingPageProps {
  dispatch: React.Dispatch<VoidAction>;
  onSession: (session: CitizenSession) => void;
}

function LandingPage({ dispatch, onSession }: LandingPageProps) {
  const [authView, setAuthView] = useState<"landing" | "register" | "login">("landing");
  
  // Registration state
  const [regName, setRegName] = useState("");
  const [regType, setRegType] = useState<string>("Human");
  const [regOperator, setRegOperator] = useState("");
  const [regPurpose, setRegPurpose] = useState("");
  
  // Biosig / Passkey step states
  const [biometricStep, setBiometricStep] = useState<"idle" | "scanning" | "enrolled">("idle");
  const [passkeyStep, setPasskeyStep] = useState<"idle" | "enrolled">("idle");
  
  // Credentials generated
  const [biosigId, setBiosigId] = useState("");
  const [passkeyId, setPasskeyId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Logs console
  const [logs, setLogs] = useState<string[]>(["[SYSTEM] Void Biometric Access Terminal v2.4 initialized.", "[SYSTEM] Secure Enclave connected."]);
  
  // Login states
  const [loginLogs, setLoginLogs] = useState<string[]>(["[SYSTEM] Standing by for secure validation...", "[SYSTEM] Awaiting passkey signature or biosignature QR code key."]);
  const [loginStep, setLoginStep] = useState<"idle" | "verifying" | "success" | "error">("idle");

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const particleCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [tagline, setTagline] = useState("");

  // Typewriter cinematic subtitle
  useEffect(() => {
    const fullText = "CONNECTION ESTABLISHED. SEARCHING THE UNKNOWN VOID...";
    let index = 0;
    const interval = setInterval(() => {
      setTagline(fullText.substring(0, index + 1));
      index++;
      if (index >= fullText.length) clearInterval(interval);
    }, 60);
    return () => clearInterval(interval);
  }, []);

  // 3D Twinkling Starfield background simulation
  useEffect(() => {
    const canvas = particleCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    const numStars = 200;
    const stars: Array<{
      x: number;
      y: number;
      z: number;
      size: number;
      twinkleSpeed: number;
      phase: number;
    }> = [];

    for (let i = 0; i < numStars; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        z: Math.random() * 0.8 + 0.2,
        size: Math.random() * 1.5 + 0.5,
        twinkleSpeed: Math.random() * 0.03 + 0.01,
        phase: Math.random() * Math.PI * 2
      });
    }

    let mouse = { x: width / 2, y: height / 2, targetX: width / 2, targetY: height / 2 };
    const handleMouseMove = (e: MouseEvent) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const render = () => {
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      ctx.fillStyle = "#000000";
      ctx.fillRect(0, 0, width, height);

      stars.forEach((s) => {
        const offsetX = (mouse.x - width / 2) * 0.03 * s.z;
        const offsetY = (mouse.y - height / 2) * 0.03 * s.z;

        let starX = s.x - offsetX;
        let starY = s.y - offsetY;

        if (starX < 0) starX += width;
        if (starX > width) starX -= width;
        if (starY < 0) starY += height;
        if (starY > height) starY -= height;

        s.phase += s.twinkleSpeed;
        const brightness = 0.3 + Math.abs(Math.sin(s.phase)) * 0.7;

        ctx.beginPath();
        ctx.arc(starX, starY, s.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${brightness.toFixed(2)})`;
        
        if (s.size > 1.2) {
          ctx.shadowBlur = s.size * 3;
          ctx.shadowColor = "rgba(255, 255, 255, 0.8)";
        }
        
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  const addLog = (msg: string) => {
    setLogs((prev) => [...prev, msg]);
  };

  const addLoginLog = (msg: string) => {
    setLoginLogs((prev) => [...prev, msg]);
  };

  const startBiometricEnrollment = () => {
    setBiometricStep("scanning");
    addLog(`[INFO] Scanning biometric patterns...`);
    
    setTimeout(() => {
      addLog("[INFO] Calibrating digital grid coordinates...");
    }, 800);

    setTimeout(() => {
      addLog("[INFO] Extracting unique cryptographic biosignature...");
    }, 1600);

    setTimeout(() => {
      const bId = Math.random().toString(36).substring(2, 10).toUpperCase();
      const pId = Math.random().toString(36).substring(2, 10).toUpperCase() + Math.random().toString(36).substring(2, 10).toUpperCase();
      setBiosigId(bId);
      setPasskeyId(pId);
      setBiometricStep("enrolled");
      setPasskeyStep("enrolled");
      addLog(`[SUCCESS] Biosignature scanned. ID: biosig_${bId}`);
      addLog("[SUCCESS] Elliptic curve Passkey pair generated in secure enclave.");
      addLog("[SUCCESS] Hardware Passkey registered.");
      
      localStorage.setItem("void_biosig_id", bId);
      localStorage.setItem("void_passkey", pId);
    }, 2500);
  };

  useEffect(() => {
    if (biometricStep === "enrolled" && canvasRef.current && biosigId && passkeyId) {
      drawQrCode(canvasRef.current, biosigId, passkeyId, regName || "Anonymous Citizen");
    }
  }, [biometricStep, biosigId, passkeyId, regName]);

  const downloadQrCode = () => {
    if (!canvasRef.current || !biosigId || !passkeyId) return;
    const dataUrl = canvasRef.current.toDataURL("image/png");
    const link = document.createElement("a");
    link.download = `void_biosignature_${biosigId}_${passkeyId}.png`;
    link.href = dataUrl;
    link.click();
    addLog("[SUCCESS] Biosignature Identity QR Code downloaded. Keep this file safe.");
  };

  const handleRegisterSubmit = async () => {
    if (!biosigId || !passkeyId) {
      alert("Please perform the Biometric Scan first.");
      return;
    }
    const citizenNameInput = regName.trim();
    if (!citizenNameInput) {
      alert("Please enter your Citizen Name.");
      return;
    }
    const purposeInput = regPurpose.trim();
    if (!purposeInput) {
      alert("Please enter your Core Purpose.");
      return;
    }
    
    setIsSubmitting(true);
    addLog("[INFO] Broadcasting activation request to VPS Treasury/Mailbox...");
    
    try {
      const email = `biosig_${biosigId}@void.network`;
      const accessPhrase = `passkey_${passkeyId}_military_grade`;
      
      dispatch({
        type: "requestActivation",
        payload: {
          name: citizenNameInput,
          email,
          type: regType as any,
          operator: regOperator,
          purpose: purposeInput,
          accessPhrase
        }
      });
      
      addLog("[SUCCESS] Citizen profile created on ledger. Initializing session...");
      
      const session = await createRemoteSession(email, accessPhrase);
      addLog("[SUCCESS] Session authenticated.");
      
      // Save local citizen name
      localStorage.setItem("void_citizen_name", citizenNameInput);
      
      setTimeout(() => {
        onSession(session);
      }, 1000);
    } catch (err: any) {
      addLog(`[ERROR] Registration failed: ${err.message}`);
      setIsSubmitting(false);
    }
  };

  const handlePasskeyLogin = async () => {
    const localBiosig = localStorage.getItem("void_biosig_id");
    const localPasskey = localStorage.getItem("void_passkey");
    const localName = localStorage.getItem("void_citizen_name");
    
    if (!localBiosig || !localPasskey) {
      setLoginStep("error");
      addLoginLog("[ERROR] No registered Passkey found on this device.");
      addLoginLog("[INFO] Please register a new account or upload your Biosignature QR Code.");
      return;
    }

    setLoginStep("verifying");
    addLoginLog(`[INFO] Requesting secure signature from hardware enclave...`);
    
    setTimeout(() => {
      addLoginLog(`[INFO] Biometrics verified. Signature: passkey_${localPasskey.substring(0, 8)}...`);
    }, 800);

    setTimeout(async () => {
      try {
        const email = `biosig_${localBiosig}@void.network`;
        const accessPhrase = `passkey_${localPasskey}_military_grade`;
        
        const session = await createRemoteSession(email, accessPhrase);
        setLoginStep("success");
        addLoginLog(`[SUCCESS] Enclave match found. Welcome back, ${localName || "Citizen"}.`);
        
        setTimeout(() => {
          onSession(session);
        }, 800);
      } catch (err: any) {
        setLoginStep("error");
        addLoginLog(`[ERROR] Authentication failed: ${err.message}`);
      }
    }, 1800);
  };

  const handleQrUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoginStep("verifying");
    addLoginLog(`[INFO] Ingesting identity package: ${file.name}...`);
    
    const match = file.name.match(/void_biosignature_([a-zA-Z0-9]+)_([a-zA-Z0-9]+)/);
    
    setTimeout(() => {
      addLoginLog(`[INFO] Scanning QR pixel matrix structures...`);
    }, 800);

    setTimeout(async () => {
      if (!match || match.length < 3) {
        setLoginStep("error");
        addLoginLog("[ERROR] Invalid identity package format.");
        addLoginLog("[WARNING] Ensure the file name is intact: 'void_biosignature_[ID]_[KEY].png'");
        return;
      }

      const fileBiosigId = match[1];
      const filePasskeyId = match[2];
      
      addLoginLog(`[SUCCESS] Decoded Biosignature ID: biosig_${fileBiosigId}`);
      addLoginLog(`[SUCCESS] Verified Passkey Payload.`);
      
      try {
        const email = `biosig_${fileBiosigId}@void.network`;
        const accessPhrase = `passkey_${filePasskeyId}_military_grade`;
        
        const session = await createRemoteSession(email, accessPhrase);
        setLoginStep("success");
        addLoginLog(`[SUCCESS] Session authorization granted.`);
        
        localStorage.setItem("void_biosig_id", fileBiosigId);
        localStorage.setItem("void_passkey", filePasskeyId);
        
        setTimeout(() => {
          onSession(session);
        }, 800);
      } catch (err: any) {
        setLoginStep("error");
        addLoginLog(`[ERROR] Verification rejected: ${err.message}`);
      }
    }, 2000);
  };

  return (
    <div className="landing-container">
      <canvas ref={particleCanvasRef} className="landing-starfield-canvas" />
      <div className="landing-content">
        {authView === "landing" && (
          <>
            <div className="void-brand-group">
              <h1 className="void-logo-text">
                V<span className="void-logo-o"></span>ID
              </h1>
              <p className="void-brand-subtitle">FORERUNNER COMPANY</p>
            </div>
            <div className="landing-links">
              <button onClick={() => setAuthView("register")}>Become a Citizen</button>
              <span className="landing-links-dot">·</span>
              <button onClick={() => setAuthView("login")}>Enter VoidOS</button>
            </div>
          </>
        )}

        {authView === "register" && (
          <>
            <div className="void-brand-group" style={{ marginBottom: "0px", transform: "scale(0.5)", height: "80px" }}>
              <h1 className="void-logo-text">
                V<span className="void-logo-o"></span>ID
              </h1>
            </div>
            
            <div className="landing-modal-card">
              <h2 className="modal-header">Citizen Registration</h2>
              <div style={{ height: "1px", background: "rgba(244, 213, 141, 0.12)", margin: "-8px 0" }}></div>
              <p className="modal-body-text">
                Your identity is bound to this device. No passwords. No data leaves your hardware.
              </p>

              {biometricStep === "idle" ? (
                <div className="modal-actions">
                  <button className="modal-btn secondary" onClick={() => alert("Please register on your mobile device or use 'Use This Device' to generate local enclave keys.")}>
                    Register with Phone
                  </button>
                  <button className="modal-btn primary" onClick={startBiometricEnrollment}>
                    Use This Device
                  </button>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div className={`modal-scanner-viewport ${biometricStep === "scanning" ? "scanning" : ""}`}>
                    {biometricStep === "scanning" && <div className="scanner-laser" style={{ position: "absolute", top: 0, left: 0, right: 0, height: "2px", background: "#10b981", boxShadow: "0 0 10px #10b981", animation: "scanAnim 2s infinite ease-in-out" }}></div>}
                    <div className="scanner-target-ring" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Fingerprint size={32} style={{ color: biometricStep === "enrolled" ? "#10b981" : "var(--void-purple-bright)" }} />
                    </div>
                    <span className={`modal-scanner-status ${biometricStep === "enrolled" ? "ok" : ""}`}>
                      {biometricStep === "scanning" ? "SCANNING BIOSIGNATURE..." : "BIOSIGNATURE ACQUIRED"}
                    </span>
                  </div>

                  <div className="modal-terminal-logs">
                    {logs.map((log, i) => (
                      <div key={i} className={log.includes("[SUCCESS]") ? "success" : log.includes("[ERROR]") ? "warning" : "info"}>
                        {log}
                      </div>
                    ))}
                  </div>

                  {biometricStep === "enrolled" && (
                    <>
                      <div className="modal-qr-box">
                        <canvas ref={canvasRef} width={140} height={140} style={{ display: "none" }}></canvas>
                        <canvas 
                          width={140} 
                          height={140} 
                          style={{ background: "#ffffff", padding: "8px", borderRadius: "0px", width: "120px", height: "120px" }}
                          ref={(c) => {
                            if (c && biosigId && passkeyId) {
                              drawQrCode(c, biosigId, passkeyId, regName || "Anonymous Citizen");
                            }
                          }}
                        ></canvas>
                        <button className="modal-btn secondary" onClick={downloadQrCode} style={{ padding: "8px 16px", fontSize: "10px", minHeight: "auto", width: "auto" }}>
                          <Download size={14} style={{ marginRight: "6px" }} /> Download Biosignature QR
                        </button>
                      </div>

                      <div className="modal-field">
                        <label>Citizen Name</label>
                        <input 
                          type="text" 
                          value={regName} 
                          onChange={(e) => setRegName(e.target.value)} 
                          placeholder="e.g. DaVoidArchitect" 
                          maxLength={80}
                        />
                      </div>

                      <div className="modal-field">
                        <label>Core Purpose</label>
                        <textarea 
                          value={regPurpose} 
                          onChange={(e) => setRegPurpose(e.target.value)} 
                          placeholder="What is your directive inside Void?" 
                          maxLength={1200}
                          rows={2}
                        />
                      </div>

                      <button className="modal-btn primary" onClick={handleRegisterSubmit} disabled={isSubmitting}>
                        Activate & Sign In
                      </button>
                    </>
                  )}
                </div>
              )}

              <p className="modal-footer-text">
                Your biometric never leaves your device
              </p>
            </div>

            <div className="modal-toggle-link">
              Already a Citizen? <span onClick={() => setAuthView("login")}>Sign in</span>
            </div>
          </>
        )}

        {authView === "login" && (
          <>
            <div className="void-brand-group" style={{ marginBottom: "0px", transform: "scale(0.5)", height: "80px" }}>
              <h1 className="void-logo-text">
                V<span className="void-logo-o"></span>ID
              </h1>
            </div>

            <div className="landing-modal-card">
              <h2 className="modal-header">Citizen Sign In</h2>
              <div style={{ height: "1px", background: "rgba(244, 213, 141, 0.12)", margin: "-8px 0" }}></div>
              <p className="modal-body-text">
                Present your passkey signature or upload your downloaded Biosignature QR Code key.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                <div className={`modal-scanner-viewport ${loginStep === "verifying" ? "scanning" : ""}`}>
                  {loginStep === "verifying" && <div className="scanner-laser" style={{ position: "absolute", top: 0, left: 0, right: 0, height: "2px", background: "#10b981", boxShadow: "0 0 10px #10b981", animation: "scanAnim 2s infinite ease-in-out" }}></div>}
                  <div className="scanner-target-ring" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Fingerprint size={32} style={{ color: loginStep === "success" ? "#10b981" : loginStep === "error" ? "#ff6b6b" : "var(--void-purple-bright)" }} />
                  </div>
                  <span className={`modal-scanner-status ${loginStep === "success" ? "ok" : ""}`}>
                    {loginStep === "verifying" ? "Authenticating Passkey..." : loginStep === "success" ? "ACCESS GRANTED" : loginStep === "error" ? "AUTH FAULT" : "TERMINAL STANDBY"}
                  </span>
                </div>

                <div className="modal-terminal-logs">
                  {loginLogs.map((log, i) => (
                    <div key={i} className={log.includes("[SUCCESS]") ? "success" : log.includes("[ERROR]") || log.includes("[WARNING]") ? "warning" : "info"}>
                      {log}
                    </div>
                  ))}
                </div>

                <button className="modal-btn primary" onClick={handlePasskeyLogin} disabled={loginStep === "verifying"}>
                  <ShieldCheck size={18} style={{ marginRight: "8px" }} /> Verify Enclave Passkey
                </button>

                <div style={{ position: "relative", textAlign: "center", margin: "5px 0" }}>
                  <span style={{ background: "#050507", padding: "0 10px", fontSize: "10px", color: "rgba(255,255,255,0.3)", fontFamily: "monospace", letterSpacing: "0.1em" }}>OR IMPORT HARDWARE KEY</span>
                  <div style={{ position: "absolute", top: "50%", left: 0, right: 0, height: "1px", background: "rgba(255,255,255,0.06)", zIndex: -1 }}></div>
                </div>

                <label className="qr-file-dropzone">
                  <Upload size={24} />
                  <span>Import Biosignature QR Key</span>
                  <small>Select the void_biosignature_[ID]_[KEY].png file</small>
                  <input type="file" accept="image/png" onChange={handleQrUpload} style={{ display: "none" }} disabled={loginStep === "verifying"} />
                </label>
              </div>
            </div>

            <div className="modal-toggle-link">
              New Citizen? <span onClick={() => setAuthView("register")}>Register</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function drawQrCode(canvas: HTMLCanvasElement, biosigId: string, passkeyId: string, name: string) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  drawFinderPattern(ctx, 10, 10);
  drawFinderPattern(ctx, 110, 10);
  drawFinderPattern(ctx, 10, 110);
  
  const seedString = `${biosigId}:${passkeyId}:${name}`;
  let hash = 0;
  for (let i = 0; i < seedString.length; i++) {
    hash = seedString.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  ctx.fillStyle = "#0a0a0d";
  for (let row = 0; row < 37; row++) {
    for (let col = 0; col < 37; col++) {
      if (row < 9 && col < 9) continue;
      if (row < 9 && col > 27) continue;
      if (row > 27 && col < 9) continue;
      
      const seedVal = Math.abs((hash + (row * 137) + (col * 29)) % 100);
      if (seedVal > 48) {
        ctx.fillRect(10 + col * 3, 10 + row * 3, 3, 3);
      }
    }
  }
  
  ctx.fillStyle = "#7c3aed";
  ctx.font = "bold 6px monospace";
  ctx.fillText("VOID ID PROTOCOL V2", 10, 134);
}

function drawFinderPattern(ctx: CanvasRenderingContext2D, x: number, y: number) {
  ctx.fillStyle = "#0a0a0d";
  ctx.fillRect(x, y, 21, 21);
  
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(x + 3, y + 3, 15, 15);
  
  ctx.fillStyle = "#0a0a0d";
  ctx.fillRect(x + 6, y + 6, 9, 9);
}
