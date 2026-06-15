import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { createVoidSeedState } from "../src/shared/voidState";
import type { VoidState } from "../src/shared/voidState";
import type { Citizen, CitizenType, ListingCategory, PulseVaults } from "../src/state/types";

export type PendingCredential = {
  requestId: string;
  email: string;
  salt: string;
  hash: string;
  createdAt: string;
};

export type ActiveCredential = {
  citizenId: string;
  email: string;
  salt: string;
  hash: string;
  activatedAt: string;
};

export type CredentialState = {
  pending: Record<string, PendingCredential>;
  activeByEmail: Record<string, ActiveCredential>;
  attemptsByEmail: Record<string, { count: number; lockedUntil: string | null; updatedAt: string }>;
};

const DATA_DIR = process.env.VOID_DATA_DIR || join(process.cwd(), ".void");
const STATE_FILE = join(DATA_DIR, "state.json");
const CREDENTIALS_FILE = join(DATA_DIR, "credentials.json");

export async function readVoidState(): Promise<VoidState> {
  try {
    const text = await readFile(STATE_FILE, "utf8");
    return normalizeState(JSON.parse(text));
  } catch {
    const seeded = normalizeState(createVoidSeedState());
    await writeVoidState(seeded);
    return seeded;
  }
}

export async function writeVoidState(state: VoidState): Promise<void> {
  await writeJsonFile(STATE_FILE, state);
}

export async function readCredentials(): Promise<CredentialState> {
  try {
    const text = await readFile(CREDENTIALS_FILE, "utf8");
    return normalizeCredentials(JSON.parse(text) as Partial<CredentialState>);
  } catch {
    return normalizeCredentials(null);
  }
}

export async function writeCredentials(credentials: CredentialState): Promise<void> {
  await writeJsonFile(CREDENTIALS_FILE, normalizeCredentials(credentials));
}

export function dataStoreInfo() {
  return {
    kind: "file",
    configured: true
  };
}

async function writeJsonFile(file: string, value: unknown) {
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function normalizeState(value: unknown): VoidState {
  const seed = createVoidSeedState();
  if (!value || typeof value !== "object") return normalizeState(seed);

  const candidate = value as Partial<VoidState>;
  const citizens = Array.isArray(candidate.citizens) && candidate.citizens.length ? candidate.citizens.map(normalizeCitizen) : seed.citizens;
  const subnets = Array.isArray(candidate.subnets) && candidate.subnets.length ? candidate.subnets : seed.subnets;
  const currentCitizenId = typeof candidate.currentCitizenId === "string" && citizens.some((citizen) => citizen.id === candidate.currentCitizenId)
    ? candidate.currentCitizenId
    : seed.currentCitizenId;

  return {
    currentCitizenId,
    activationRequests: Array.isArray(candidate.activationRequests) ? candidate.activationRequests : [],
    citizens,
    subnets,
    quests: Array.isArray(candidate.quests) ? candidate.quests : [],
    marketplace: Array.isArray(candidate.marketplace) ? candidate.marketplace : seed.marketplace,
    ledger: Array.isArray(candidate.ledger) ? candidate.ledger : [],
    pulseVaults: normalizePulseVaults(candidate.pulseVaults),
    impactEvents: Array.isArray(candidate.impactEvents) ? candidate.impactEvents : [],
    legacy: Array.isArray(candidate.legacy) ? candidate.legacy : [],
    audit: Array.isArray(candidate.audit) ? candidate.audit : [],
    feedback: Array.isArray(candidate.feedback) ? candidate.feedback : [],
    mesh: candidate.mesh || {
      mass: 10000.0,
      energy: 36000000.0, // 36 MJ = 10 kWh initial
      entropy: 0.1,
      cycle: 0.95
    }
  } as VoidState;
}

function normalizeCredentials(value: Partial<CredentialState> | null | undefined): CredentialState {
  return {
    pending: value?.pending && typeof value.pending === "object" ? value.pending : {},
    activeByEmail: value?.activeByEmail && typeof value.activeByEmail === "object" ? value.activeByEmail : {},
    attemptsByEmail: value?.attemptsByEmail && typeof value.attemptsByEmail === "object" ? value.attemptsByEmail : {}
  };
}

function normalizePulseVaults(value: Partial<PulseVaults> | undefined): PulseVaults {
  return {
    ubi: Number(value?.ubi || 0),
    infrastructure: Number(value?.infrastructure || 0),
    operating: Number(value?.operating || 0)
  };
}

function normalizeCitizen(citizen: Citizen): Citizen {
  return {
    ...citizen,
    aiCompanion: citizen.aiCompanion || buildAICompanionProfile(citizen.name, citizen.type, "Contribute to Void."),
    onboardingPlan: citizen.onboardingPlan || buildOnboardingPlan(citizen.type, "Contribute to Void.", citizen.createdAt)
  };
}

function buildAICompanionProfile(name: string, type: CitizenType, purpose: string) {
  return {
    name: `${name.split(" ")[0] || "Citizen"}'s Void AI`,
    mode: type === "AI Agent" ? "Operator-Supervised Agent" as const : type === "Organization" ? "Organization Steward" as const : "Local Companion" as const,
    onboardingStage: "New" as const,
    directives: [
      "Protect the citizen's private context and platform trade secrets.",
      "Help convert intent into quests, listings, proof, and useful contribution.",
      "Respect Void platform law, capability boundaries, and accountable operator rules."
    ],
    learningFocus: deriveLearningFocus(type, purpose)
  };
}

function buildOnboardingPlan(type: CitizenType, purpose: string, createdAt: string) {
  const lowerPurpose = purpose.toLowerCase();
  const suggestedListingCategory: ListingCategory = lowerPurpose.includes("compute") || lowerPurpose.includes("gpu")
    ? "Compute"
    : lowerPurpose.includes("course") || lowerPurpose.includes("teach") || lowerPurpose.includes("learn")
      ? "Training"
      : lowerPurpose.includes("product") || lowerPurpose.includes("sell")
        ? "Product"
        : type === "AI Agent"
          ? "Model"
          : "Service";

  return {
    stage: "Orientation" as const,
    nextActions: [
      "Complete citizen profile and define the first useful intent.",
      "Join or create a subnet aligned with the citizen's purpose.",
      "Publish one quest or marketplace listing that creates verifiable value.",
      "Submit proof after the first contribution so impact can become legacy."
    ],
    suggestedQuestClass: suggestedListingCategory === "Training" ? "Mentorship" : suggestedListingCategory === "Compute" ? "Infrastructure" : "Builder",
    suggestedListingCategory,
    createdAt
  };
}

function deriveLearningFocus(type: CitizenType, purpose: string) {
  const focus = ["Void law", "proof habits", "impact growth"];
  const lowerPurpose = purpose.toLowerCase();
  if (type === "AI Agent") focus.push("operator accountability");
  if (lowerPurpose.includes("compute") || lowerPurpose.includes("gpu")) focus.push("resource marketplace");
  if (lowerPurpose.includes("teach") || lowerPurpose.includes("learn")) focus.push("training paths");
  if (lowerPurpose.includes("product") || lowerPurpose.includes("sell")) focus.push("product listings");
  return focus.slice(0, 5);
}

