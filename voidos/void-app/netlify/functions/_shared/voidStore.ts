import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";
import { createVoidSeedState } from "../../../src/shared/voidState";
import type { VoidState } from "../../../src/shared/voidState";
import type { Citizen, CitizenType, ListingCategory, PulseVaults } from "../../../src/state/types";
import { readJsonRecord, writeJsonRecord } from "./supabaseStore";

const STORE_NAME = "void-alpha-state";
const STATE_KEY = "state.json";
const DATABASE_STATE_KEY = "alpha_state";
const LOCAL_STATE_FILE = join(process.cwd(), ".netlify", "local-void-alpha-state.json");
const TMP_STATE_FILE = join(tmpdir(), "void-alpha-local-development-state.json");

type BlobStore = {
  get: (key: string, options: { type: "json" }) => Promise<unknown | null>;
  setJSON: (key: string, value: unknown) => Promise<unknown>;
};

export async function readVoidState(): Promise<VoidState> {
  const databaseState = await readJsonRecord<VoidState>(DATABASE_STATE_KEY);
  if (databaseState) return normalizeState(databaseState);

  const store = await getBlobStore();
  if (store) {
    const stored = await store.get(STATE_KEY, { type: "json" });
    return normalizeState(stored);
  }

  return readLocalDevelopmentState();
}

export async function writeVoidState(state: VoidState): Promise<void> {
  if (await writeJsonRecord(DATABASE_STATE_KEY, state)) return;

  const store = await getBlobStore();
  if (store) {
    await store.setJSON(STATE_KEY, state);
    return;
  }

  await writeLocalDevelopmentState(state);
}

async function getBlobStore(): Promise<BlobStore | null> {
  try {
    const blobs = await import("@netlify/blobs");
    return blobs.getStore({ name: STORE_NAME, consistency: "strong" }) as unknown as BlobStore;
  } catch {
    return null;
  }
}

async function readLocalDevelopmentState(): Promise<VoidState> {
  for (const file of [LOCAL_STATE_FILE, TMP_STATE_FILE]) {
    try {
      const text = await readFile(file, "utf8");
      return normalizeState(JSON.parse(text));
    } catch {
      continue;
    }
  }

  const seeded = createVoidSeedState();
  await writeLocalDevelopmentState(seeded);
  return seeded;
}

async function writeLocalDevelopmentState(state: VoidState): Promise<void> {
  const target = process.env.NETLIFY ? TMP_STATE_FILE : LOCAL_STATE_FILE;
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, JSON.stringify(state, null, 2), "utf8");
}

function normalizeState(value: unknown): VoidState {
  const seed = createVoidSeedState();
  if (!value || typeof value !== "object") return seed;

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
    feedback: Array.isArray(candidate.feedback) ? candidate.feedback : []
  } as VoidState;
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
