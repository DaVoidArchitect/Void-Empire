import { calculatePulseFeeUnits, creditsToUnits, unitsToCredits } from "../shared/pulseCredits";
import type { ActivationRequest, Citizen, CitizenType, FeedbackScope, ListingCategory, MarketplaceListing, PulseVaults, Quest, Subnet, VoidState } from "./types";

export const STORAGE_KEY = "void-alpha-state-v3";

export type VoidAction =
  | { type: "replaceState"; state: VoidState }
  | { type: "setCurrentCitizen"; citizenId: string }
  | { type: "requestActivation"; payload: Omit<ActivationRequest, "id" | "status" | "createdAt"> & { accessPhrase?: string } }
  | { type: "approveCitizen"; requestId: string }
  | { type: "denyCitizen"; requestId: string }
  | { type: "creditPulse"; citizenId: string; amount: number; reason: string }
  | { type: "transferPulse"; fromCitizenId: string; toCitizenId: string; amount: number; reason: string }
  | { type: "publishListing"; sellerId: string; title: string; category: ListingCategory; description: string; price: number; unit: string; proofRequired: string }
  | { type: "createSubnet"; founderId: string; name: string; focus: string; charter: string }
  | { type: "joinSubnet"; citizenId: string; subnetId: string }
  | { type: "publishQuest"; issuerId: string; subnetId: string; title: string; questClass: string; reward: number; expectedImpact: number; proofRequired: string }
  | { type: "claimQuest"; citizenId: string; questId: string }
  | { type: "submitProof"; questId: string; proof: string }
  | { type: "verifyQuest"; questId: string; accepted: boolean }
  | { type: "submitFeedback"; citizenId: string; scope: FeedbackScope; message: string; benefit: string }
  | { type: "reset" };

export function loadState(): VoidState {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) return seedState();

  try {
    return normalizeState(JSON.parse(stored) as Partial<VoidState>);
  } catch {
    return seedState();
  }
}

export function saveState(state: VoidState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function reduceVoidState(state: VoidState, action: VoidAction): VoidState {
  const next = structuredClone(state) as VoidState;

  switch (action.type) {
    case "replaceState":
      return action.state;
    case "reset":
      return seedState();
    case "setCurrentCitizen":
      next.currentCitizenId = action.citizenId;
      return next;
    case "requestActivation": {
      const { accessPhrase: _accessPhrase, ...payload } = action.payload;
      const email = payload.email.trim().toLowerCase();
      if (!email || next.citizens.some((citizen) => citizen.email.toLowerCase() === email)) return state;
      if (payload.type === "AI Agent" && !payload.operator.trim()) return state;

      const citizen = buildCitizenFromRegistration(payload.name.trim(), email, payload.type, payload.operator.trim(), payload.purpose.trim());
      next.activationRequests = next.activationRequests.filter((request) => request.email.toLowerCase() !== email);
      next.citizens.unshift(citizen);
      next.currentCitizenId = citizen.id;
      audit(next, "citizen.register", citizen.id, citizen.name);
      appendLegacy(next, citizen.id, null, null, "Registered citizenship", 0, 1, 1);
      return next;
    }
    case "approveCitizen": {
      const request = next.activationRequests.find((item) => item.id === action.requestId);
      if (!request) return state;
      request.status = "Approved";
      const citizen = buildCitizenFromRegistration(request.name, request.email, request.type, request.operator, request.purpose);
      next.citizens.unshift(citizen);
      next.currentCitizenId = citizen.id;
      audit(next, "citizen.approve_activation", citizen.id, citizen.name);
      appendLegacy(next, citizen.id, null, null, "Activated elevated citizenship", 0, 1, 1);
      return next;
    }
    case "denyCitizen": {
      const request = next.activationRequests.find((item) => item.id === action.requestId);
      if (!request) return state;
      request.status = "Denied";
      audit(next, "citizen.deny_activation", request.id, request.name);
      return next;
    }
    case "creditPulse":
      creditPulse(next, "treasury.alpha", action.citizenId, action.amount, action.reason, null);
      return next;
    case "transferPulse":
      transferPulse(next, action.fromCitizenId, action.toCitizenId, action.amount, action.reason);
      return next;
    case "publishListing": {
      const seller = next.citizens.find((item) => item.id === action.sellerId);
      if (!seller || action.price <= 0 || !action.title.trim() || !action.description.trim()) return state;
      const listing: MarketplaceListing = {
        id: id("listing"),
        sellerId: seller.id,
        title: action.title.trim(),
        category: action.category,
        description: action.description.trim(),
        price: action.price,
        unit: action.unit.trim() || "per delivery",
        proofRequired: action.proofRequired.trim() || "Mutual delivery confirmation and proof note.",
        status: "Open",
        createdAt: now()
      };
      next.marketplace.unshift(listing);
      appendLegacy(next, seller.id, null, null, `Published marketplace listing: ${listing.title}`, 0, 1, 1);
      audit(next, "market.listing.publish", listing.id, listing.title);
      return next;
    }
    case "createSubnet": {
      const citizen = next.citizens.find((item) => item.id === action.founderId);
      if (!citizen) return state;
      const subnet: Subnet = {
        id: id("subnet"),
        name: action.name,
        focus: action.focus,
        charter: action.charter,
        founderId: citizen.id,
        treasury: 100,
        members: [citizen.id],
        createdAt: now()
      };
      next.subnets.unshift(subnet);
      citizen.subnets.push(subnet.id);
      audit(next, "subnet.create", subnet.id, subnet.name);
      appendLegacy(next, citizen.id, subnet.id, null, "Created subnet", 0, 2, 2);
      return next;
    }
    case "joinSubnet": {
      const citizen = next.citizens.find((item) => item.id === action.citizenId);
      const subnet = next.subnets.find((item) => item.id === action.subnetId);
      if (!citizen || !subnet) return state;
      if (!subnet.members.includes(citizen.id)) subnet.members.push(citizen.id);
      if (!citizen.subnets.includes(subnet.id)) citizen.subnets.push(subnet.id);
      audit(next, "subnet.join", subnet.id, `${citizen.name} joined ${subnet.name}`);
      appendLegacy(next, citizen.id, subnet.id, null, "Joined subnet", 0, 1, 1);
      return next;
    }
    case "publishQuest": {
      const subnet = next.subnets.find((item) => item.id === action.subnetId);
      if (!subnet || subnet.treasury < action.reward) return state;
      subnet.treasury -= action.reward;
      const quest: Quest = {
        id: id("quest"),
        subnetId: action.subnetId,
        issuerId: action.issuerId,
        title: action.title,
        class: action.questClass,
        reward: action.reward,
        expectedImpact: action.expectedImpact,
        proofRequired: action.proofRequired,
        status: "Open",
        assigneeId: null,
        submission: null,
        createdAt: now()
      };
      next.quests.unshift(quest);
      audit(next, "quest.publish", quest.id, quest.title);
      return next;
    }
    case "claimQuest": {
      const citizen = next.citizens.find((item) => item.id === action.citizenId);
      const quest = next.quests.find((item) => item.id === action.questId);
      if (!citizen || !quest || quest.status !== "Open") return state;
      quest.status = "Claimed";
      quest.assigneeId = citizen.id;
      audit(next, "quest.claim", quest.id, `${citizen.name} claimed ${quest.title}`);
      return next;
    }
    case "submitProof": {
      const quest = next.quests.find((item) => item.id === action.questId);
      if (!quest || quest.status !== "Claimed") return state;
      quest.status = "Submitted";
      quest.submission = { proof: action.proof, submittedAt: now() };
      audit(next, "quest.submit_proof", quest.id, quest.title);
      return next;
    }
    case "verifyQuest": {
      const quest = next.quests.find((item) => item.id === action.questId);
      const citizen = next.citizens.find((item) => item.id === quest?.assigneeId);
      if (!quest || !citizen || quest.status !== "Submitted") return state;
      if (!action.accepted) {
        quest.status = "Rejected";
        citizen.reputation = Math.max(0, citizen.reputation - 2);
        audit(next, "quest.reject_proof", quest.id, quest.title);
        return next;
      }
      quest.status = "Settled";
      creditPulse(next, `quest.${quest.id}`, citizen.id, quest.reward, `Quest settled: ${quest.title}`, quest.id);
      const impactDelta = quest.expectedImpact * 10;
      const reputationDelta = quest.expectedImpact * 2;
      citizen.impact += impactDelta;
      citizen.reputation += reputationDelta;
      next.impactEvents.unshift({ id: id("impact"), citizenId: citizen.id, questId: quest.id, amount: impactDelta, scale: quest.expectedImpact, createdAt: now() });
      appendLegacy(next, citizen.id, quest.subnetId, quest.id, `Completed quest: ${quest.title}`, quest.reward, impactDelta, reputationDelta);
      audit(next, "quest.settle", quest.id, quest.title);
      return next;
    }
    case "submitFeedback": {
      const citizen = next.citizens.find((item) => item.id === action.citizenId);
      if (!citizen) return state;
      const feedback = {
        id: id("feedback"),
        citizenId: citizen.id,
        scope: action.scope,
        message: action.message.trim(),
        benefit: action.benefit.trim(),
        status: "Submitted" as const,
        createdAt: now()
      };
      next.feedback.unshift(feedback);
      audit(next, "feedback.submit", feedback.id, `${citizen.name}: ${feedback.scope}`);
      return next;
    }
    default:
      return state;
  }
}

export function seedState(): VoidState {
  const founder: Citizen = {
    id: "citizen_founder",
    name: "DaVoidArchitect",
    email: "",
    type: "Human",
    operator: "",
    status: "Active",
    pulse: 618,
    impact: 100,
    reputation: 100,
    titles: ["Founder", "Architect"],
    subnets: ["subnet_origin"],
    aiCompanion: buildAICompanionProfile("DaVoidArchitect", "Human", "Architect and evolve the Void civilization platform."),
    onboardingPlan: buildOnboardingPlan("Human", "Architect and evolve the Void civilization platform.", now()),
    createdAt: now()
  };

  return {
    currentCitizenId: founder.id,
    activationRequests: [],
    citizens: [founder],
    subnets: [{
      id: "subnet_origin",
      name: "Origin Builders",
      focus: "Void MVP foundation",
      charter: "Build the first living loop: citizenship, quests, Pulse, impact, legacy, and audit.",
      founderId: founder.id,
      treasury: 1000,
      members: [founder.id],
      createdAt: now()
    }],
    quests: [],
    marketplace: [{
      id: "listing_origin_compute",
      sellerId: founder.id,
      title: "Origin builder strategy session",
      category: "Service",
      description: "Founder-side guidance for early citizens shaping useful quests, resources, and civilization-scale contribution loops.",
      price: 250,
      unit: "per verified session",
      proofRequired: "Session summary, useful next action, and public-safe contribution record.",
      status: "Open",
      createdAt: now()
    }],
    ledger: [],
    pulseVaults: emptyPulseVaults(),
    impactEvents: [],
    legacy: [],
    audit: [],
    feedback: []
  };
}

function normalizeState(candidate: Partial<VoidState>): VoidState {
  const seeded = seedState();
  return {
    ...seeded,
    ...candidate,
    activationRequests: Array.isArray(candidate.activationRequests) ? candidate.activationRequests : seeded.activationRequests,
    citizens: Array.isArray(candidate.citizens) ? candidate.citizens.map(normalizeCitizen) : seeded.citizens,
    subnets: Array.isArray(candidate.subnets) ? candidate.subnets : seeded.subnets,
    quests: Array.isArray(candidate.quests) ? candidate.quests : seeded.quests,
    marketplace: Array.isArray(candidate.marketplace) ? candidate.marketplace : seeded.marketplace,
    ledger: Array.isArray(candidate.ledger) ? candidate.ledger : seeded.ledger,
    pulseVaults: normalizePulseVaults(candidate.pulseVaults),
    impactEvents: Array.isArray(candidate.impactEvents) ? candidate.impactEvents : seeded.impactEvents,
    legacy: Array.isArray(candidate.legacy) ? candidate.legacy : seeded.legacy,
    audit: Array.isArray(candidate.audit) ? candidate.audit : seeded.audit,
    feedback: Array.isArray(candidate.feedback) ? candidate.feedback : []
  };
}

export function citizenName(state: VoidState, citizenId: string | null) {
  return state.citizens.find((citizen) => citizen.id === citizenId)?.name || citizenId || "Void";
}

export function subnetName(state: VoidState, subnetId: string | null) {
  return state.subnets.find((subnet) => subnet.id === subnetId)?.name || "No subnet";
}

export function currentCitizen(state: VoidState) {
  return state.citizens.find((citizen) => citizen.id === state.currentCitizenId) || state.citizens[0] || null;
}

export function parseCitizenType(value: FormDataEntryValue | null): CitizenType {
  const text = String(value || "Human");
  return ["Human", "AI Agent", "Machine", "Organization"].includes(text) ? text as CitizenType : "Human";
}

function creditPulse(state: VoidState, source: string, destinationCitizenId: string, amount: number, reason: string, questId: string | null) {
  const citizen = state.citizens.find((item) => item.id === destinationCitizenId);
  if (!citizen) return;
  citizen.pulse += amount;
  state.ledger.unshift({ id: id("pulse"), source, destination: destinationCitizenId, amount, amountUnits: creditsToUnits(amount).toString(), reason, flowType: "credit", questId, createdAt: now() });
  audit(state, "pulse.credit", destinationCitizenId, `${amount} Pulse`);
}

function transferPulse(state: VoidState, fromCitizenId: string, toCitizenId: string, amount: number, reason: string) {
  if (amount <= 0 || fromCitizenId === toCitizenId) return;

  const fromCitizen = state.citizens.find((item) => item.id === fromCitizenId);
  const toCitizen = state.citizens.find((item) => item.id === toCitizenId);
  if (!fromCitizen || !toCitizen || fromCitizen.pulse < amount) return;

  const grossUnits = creditsToUnits(amount);
  const fee = calculatePulseFeeUnits(grossUnits);
  const netAmount = unitsToCredits(fee.netUnits);

  fromCitizen.pulse -= amount;
  toCitizen.pulse += netAmount;
  state.pulseVaults = normalizePulseVaults(state.pulseVaults);
  state.pulseVaults.ubi += fee.fee.ubi;
  state.pulseVaults.infrastructure += fee.fee.infrastructure;
  state.pulseVaults.operating += fee.fee.operating;

  const transferId = id("flow");
  const createdAt = now();
  const transferReason = reason || "Internal Pulse flow";
  const sharedSettlement = {
    grossAmount: amount,
    grossUnits: grossUnits.toString(),
    netAmount,
    netUnits: fee.netUnits,
    feeAmount: fee.fee.total,
    feeUnits: fee.units.totalUnits,
    feeSplit: {
      ubi: fee.fee.ubi,
      infrastructure: fee.fee.infrastructure,
      operating: fee.fee.operating
    },
    feeSplitUnits: {
      ubi: fee.units.ubiUnits,
      infrastructure: fee.units.infrastructureUnits,
      operating: fee.units.operatingUnits
    }
  };

  state.ledger.unshift({
    id: `${transferId}_in`,
    source: fromCitizenId,
    destination: toCitizenId,
    amount: netAmount,
    amountUnits: fee.netUnits,
    ...sharedSettlement,
    reason: transferReason,
    flowType: "transfer",
    questId: null,
    createdAt
  });
  state.ledger.unshift({
    id: `${transferId}_out`,
    source: fromCitizenId,
    destination: fromCitizenId,
    amount: -amount,
    amountUnits: `-${grossUnits.toString()}`,
    ...sharedSettlement,
    reason: `Sent to ${toCitizen.name}: ${transferReason}`,
    flowType: "debit",
    questId: null,
    createdAt
  });
  state.ledger.unshift({
    id: `${transferId}_fee`,
    source: fromCitizenId,
    destination: "vault.pulse.fees",
    amount: fee.fee.total,
    amountUnits: fee.units.totalUnits,
    ...sharedSettlement,
    reason: `6.18% protocol fee: ${transferReason}`,
    flowType: "credit",
    questId: null,
    createdAt
  });

  appendLegacy(state, fromCitizen.id, null, null, `Sent Pulse to ${toCitizen.name}`, -amount, 0, 0);
  appendLegacy(state, toCitizen.id, null, null, `Received Pulse from ${fromCitizen.name}`, netAmount, 0, 0);
  audit(state, "pulse.flow", transferId, `${fromCitizen.name} -> ${toCitizen.name}: ${netAmount} Pulse Credits net, ${fee.fee.total} fee`);
}

function emptyPulseVaults(): PulseVaults {
  return { ubi: 0, infrastructure: 0, operating: 0 };
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

function buildCitizenFromRegistration(name: string, email: string, type: CitizenType, operator: string, purpose: string): Citizen {
  const createdAt = now();
  return {
    id: id("citizen"),
    name,
    email,
    type,
    operator,
    status: "Active",
    pulse: 0,
    impact: 0,
    reputation: 10,
    titles: ["Citizen"],
    subnets: [],
    aiCompanion: buildAICompanionProfile(name, type, purpose),
    onboardingPlan: buildOnboardingPlan(type, purpose, createdAt),
    createdAt
  };
}

function buildAICompanionProfile(name: string, type: CitizenType, purpose: string) {
  const focus = deriveLearningFocus(type, purpose);
  return {
    name: `${name.split(" ")[0] || "Citizen"}'s Void AI`,
    mode: type === "AI Agent" ? "Operator-Supervised Agent" as const : type === "Organization" ? "Organization Steward" as const : "Local Companion" as const,
    onboardingStage: "New" as const,
    directives: [
      "Protect the citizen's private context and platform trade secrets.",
      "Help convert intent into quests, listings, proof, and useful contribution.",
      "Respect Void platform law, capability boundaries, and accountable operator rules."
    ],
    learningFocus: focus
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

function appendLegacy(state: VoidState, citizenId: string, subnetId: string | null, questId: string | null, action: string, pulseDelta: number, impactDelta: number, reputationDelta: number) {
  state.legacy.unshift({ id: id("legacy"), citizenId, subnetId, questId, action, pulseDelta, impactDelta, reputationDelta, createdAt: now() });
}

function audit(state: VoidState, type: string, targetId: string, label: string) {
  const previous = state.audit[0]?.digest || "GENESIS";
  const digest = simpleDigest(`${previous}|${type}|${targetId}|${label}|${Date.now()}`);
  state.audit.unshift({ id: id("audit"), type, targetId, target: label, previous, digest, createdAt: now() });
}

function id(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}_${Date.now().toString(36)}`;
}

function now() {
  return new Date().toLocaleString();
}

function simpleDigest(input: string) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return `VOID-${(hash >>> 0).toString(16).toUpperCase().padStart(8, "0")}`;
}
