import type {
  ActivationRequest,
  AuditEvent,
  Citizen,
  CitizenType,
  FeedbackScope,
  ImpactEvent,
  LegacyEvent,
  ListingCategory,
  MarketplaceListing,
  PulseLedgerEvent,
  PulseVaults,
  Quest,
  Subnet,
  VoidState
} from "../state/types";
import { calculatePulseFeeUnits, creditsToUnits, unitsToCredits } from "./pulseCredits";

export type VoidApiAction =
  | { type: "requestActivation"; payload: { name: string; email: string; type: CitizenType; operator: string; purpose: string; accessPhrase?: string } }
  | { type: "approveCitizen"; requestId: string }
  | { type: "denyCitizen"; requestId: string }
  | { type: "createSubnet"; founderId: string; name: string; focus: string; charter: string }
  | { type: "joinSubnet"; citizenId: string; subnetId: string }
  | { type: "publishQuest"; issuerId: string; subnetId: string; title: string; questClass: string; reward: number; expectedImpact: number; proofRequired: string }
  | { type: "claimQuest"; citizenId: string; questId: string }
  | { type: "submitProof"; questId: string; proof: string }
  | { type: "verifyQuest"; questId: string; accepted: boolean }
  | { type: "creditPulse"; citizenId: string; amount: number; reason: string }
  | { type: "flowPulse"; fromCitizenId: string; toCitizenId: string; amount: number; reason: string }
  | { type: "publishListing"; sellerId: string; title: string; category: ListingCategory; description: string; price: number; unit: string; proofRequired: string }
  | { type: "submitFeedback"; citizenId: string; scope: FeedbackScope; message: string; benefit: string };

export type VoidApiResult = {
  state: VoidState;
  event: AuditEvent | null;
};

export type VoidCapability =
  | "admin.activation.approve"
  | "admin.activation.deny"
  | "admin.pulse.grant"
  | "quest.verify"
  | "subnet.create"
  | "subnet.join"
  | "quest.publish"
  | "quest.claim"
  | "quest.proof.submit"
  | "pulse.flow"
  | "market.listing.publish"
  | "feedback.submit";

export type VoidActor = {
  citizenId: string;
  isAdmin: boolean;
};

export function createVoidSeedState(): VoidState {
  const createdAt = now();
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
    onboardingPlan: buildOnboardingPlan("Human", "Architect and evolve the Void civilization platform.", createdAt),
    createdAt
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
      createdAt
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
      createdAt
    }],
    ledger: [],
    pulseVaults: emptyPulseVaults(),
    impactEvents: [],
    legacy: [],
    audit: [],
    feedback: []
  };
}

export function authorizeVoidApiAction(state: VoidState, action: VoidApiAction, actor: VoidActor | null): VoidApiAction {
  if (action.type === "requestActivation") return action;

  if (!actor?.citizenId) {
    throw new Error("A Void actor identity is required for this action.");
  }

  const capabilities = capabilitiesForActor(state, actor);

  switch (action.type) {
    case "approveCitizen":
      requireCapability(capabilities, "admin.activation.approve");
      return action;
    case "denyCitizen":
      requireCapability(capabilities, "admin.activation.deny");
      return action;
    case "creditPulse":
      requireCapability(capabilities, "admin.pulse.grant");
      return action;
    case "verifyQuest":
      requireCapability(capabilities, "quest.verify");
      return action;
    case "createSubnet":
      requireCapability(capabilities, "subnet.create");
      assertActorOwns(action.founderId, actor.citizenId, "Citizens can only create subnets as themselves.");
      return action;
    case "joinSubnet":
      requireCapability(capabilities, "subnet.join");
      assertActorOwns(action.citizenId, actor.citizenId, "Citizens can only join subnets as themselves.");
      return action;
    case "publishQuest":
      requireCapability(capabilities, "quest.publish");
      assertActorOwns(action.issuerId, actor.citizenId, "Citizens can only publish quests as themselves.");
      return action;
    case "claimQuest":
      requireCapability(capabilities, "quest.claim");
      assertActorOwns(action.citizenId, actor.citizenId, "Citizens can only claim quests as themselves.");
      return action;
    case "submitProof":
      requireCapability(capabilities, "quest.proof.submit");
      assertActorIsQuestAssignee(state, action.questId, actor.citizenId);
      return action;
    case "flowPulse":
      requireCapability(capabilities, "pulse.flow");
      assertActorOwns(action.fromCitizenId, actor.citizenId, "Citizens can only send Pulse from their own internal balance.");
      return action;
    case "publishListing":
      requireCapability(capabilities, "market.listing.publish");
      assertActorOwns(action.sellerId, actor.citizenId, "Citizens can only publish marketplace listings as themselves.");
      return action;
    case "submitFeedback":
      requireCapability(capabilities, "feedback.submit");
      assertActorOwns(action.citizenId, actor.citizenId, "Citizens can only submit feedback as themselves.");
      return action;
    default:
      return action;
  }
}

export function applyVoidApiAction(state: VoidState, action: VoidApiAction): VoidApiResult {
  const next = cloneState(state);

  switch (action.type) {
    case "requestActivation": {
      const name = boundedText(action.payload.name, "Citizen name is required.", 80);
      const email = boundedEmail(action.payload.email);
      const operator = optionalBoundedText(action.payload.operator, 120);
      const purpose = boundedText(action.payload.purpose, "Citizen purpose is required.", 1200);
      assertCitizenType(action.payload.type);
      if (action.payload.type === "AI Agent" && !operator) {
        throw new Error("AI agent registrations need an accountable operator or sponsor.");
      }
      if (next.citizens.some((citizen) => citizen.email.toLowerCase() === email)) {
        throw new Error("A citizen already exists for this email.");
      }
      next.activationRequests = next.activationRequests.filter((request) => request.email.toLowerCase() !== email);

      const citizen = buildCitizenFromRegistration(name, email, action.payload.type, operator, purpose);
      next.citizens.unshift(citizen);
      next.currentCitizenId = citizen.id;
      appendLegacy(next, citizen.id, null, null, "Registered citizenship", 0, 1, 1);
      return withAudit(next, "citizen.register", citizen.id, citizen.name);
    }
    case "approveCitizen": {
      const request = findRequired(next.activationRequests, action.requestId, "Activation request was not found.");
      if (request.status === "Approved") throw new Error("Activation request is already approved.");
      if (request.status === "Denied") throw new Error("Denied activation requests cannot be approved.");
      if (next.citizens.some((citizen) => citizen.email.toLowerCase() === request.email.toLowerCase())) {
        throw new Error("A citizen already exists for this email.");
      }

      request.status = "Approved";
      const citizen = buildCitizenFromRegistration(request.name, request.email, request.type, request.operator, request.purpose);
      next.citizens.unshift(citizen);
      appendLegacy(next, citizen.id, null, null, "Activated elevated citizenship", 0, 1, 1);
      return withAudit(next, "citizen.approve_activation", citizen.id, citizen.name);
    }
    case "denyCitizen": {
      const request = findRequired(next.activationRequests, action.requestId, "Activation request was not found.");
      if (request.status === "Approved") throw new Error("Approved activation requests cannot be denied.");
      request.status = "Denied";
      return withAudit(next, "citizen.deny_activation", request.id, request.name);
    }
    case "createSubnet": {
      const citizen = findRequired(next.citizens, action.founderId, "Founder citizen was not found.");
      assertText(action.name, "Subnet name is required.");
      assertText(action.focus, "Subnet focus is required.");
      assertText(action.charter, "Subnet charter is required.");

      const subnet: Subnet = {
        id: id("subnet"),
        name: action.name.trim(),
        focus: action.focus.trim(),
        charter: action.charter.trim(),
        founderId: citizen.id,
        treasury: 100,
        members: [citizen.id],
        createdAt: now()
      };
      next.subnets.unshift(subnet);
      addUnique(citizen.subnets, subnet.id);
      appendLegacy(next, citizen.id, subnet.id, null, "Created subnet", 0, 2, 2);
      return withAudit(next, "subnet.create", subnet.id, subnet.name);
    }
    case "joinSubnet": {
      const citizen = findRequired(next.citizens, action.citizenId, "Citizen was not found.");
      const subnet = findRequired(next.subnets, action.subnetId, "Subnet was not found.");
      addUnique(subnet.members, citizen.id);
      addUnique(citizen.subnets, subnet.id);
      appendLegacy(next, citizen.id, subnet.id, null, "Joined subnet", 0, 1, 1);
      return withAudit(next, "subnet.join", subnet.id, `${citizen.name} joined ${subnet.name}`);
    }
    case "publishQuest": {
      const issuer = findRequired(next.citizens, action.issuerId, "Issuer citizen was not found.");
      const subnet = findRequired(next.subnets, action.subnetId, "Subnet was not found.");
      assertText(action.title, "Quest title is required.");
      assertPositive(action.reward, "Quest reward must be greater than zero.");
      assertPositive(action.expectedImpact, "Expected impact must be greater than zero.");
      assertText(action.proofRequired, "Proof requirement is required.");
      if (!subnet.members.includes(issuer.id)) throw new Error("Issuer must belong to the subnet.");
      if (subnet.treasury < action.reward) throw new Error("Subnet treasury does not have enough internal Pulse Credits for this quest.");

      subnet.treasury -= action.reward;
      const quest: Quest = {
        id: id("quest"),
        subnetId: subnet.id,
        issuerId: issuer.id,
        title: action.title.trim(),
        class: (action.questClass || "Build").trim(),
        reward: action.reward,
        expectedImpact: action.expectedImpact,
        proofRequired: action.proofRequired.trim(),
        status: "Open",
        assigneeId: null,
        submission: null,
        createdAt: now()
      };
      next.quests.unshift(quest);
      return withAudit(next, "quest.publish", quest.id, quest.title);
    }
    case "claimQuest": {
      const citizen = findRequired(next.citizens, action.citizenId, "Citizen was not found.");
      const quest = findRequired(next.quests, action.questId, "Quest was not found.");
      const subnet = findRequired(next.subnets, quest.subnetId, "Quest subnet was not found.");
      if (quest.status !== "Open") throw new Error("Quest is not open for claim.");
      if (!subnet.members.includes(citizen.id)) throw new Error("Citizen must belong to the quest subnet.");
      quest.status = "Claimed";
      quest.assigneeId = citizen.id;
      return withAudit(next, "quest.claim", quest.id, `${citizen.name} claimed ${quest.title}`);
    }
    case "submitProof": {
      const quest = findRequired(next.quests, action.questId, "Quest was not found.");
      assertText(action.proof, "Quest proof is required.");
      if (quest.status !== "Claimed") throw new Error("Only claimed quests can receive proof.");
      quest.status = "Submitted";
      quest.submission = { proof: action.proof.trim(), submittedAt: now() };
      return withAudit(next, "quest.submit_proof", quest.id, quest.title);
    }
    case "verifyQuest": {
      const quest = findRequired(next.quests, action.questId, "Quest was not found.");
      const citizen = findRequired(next.citizens, quest.assigneeId, "Assigned citizen was not found.");
      if (quest.status !== "Submitted") throw new Error("Only submitted quests can be verified.");

      if (!action.accepted) {
        quest.status = "Rejected";
        citizen.reputation = Math.max(0, citizen.reputation - 2);
        return withAudit(next, "quest.reject_proof", quest.id, quest.title);
      }

      quest.status = "Settled";
      creditPulse(next, `quest.${quest.id}`, citizen.id, quest.reward, `Quest settled: ${quest.title}`, quest.id);
      const impactDelta = quest.expectedImpact * 10;
      const reputationDelta = quest.expectedImpact * 2;
      citizen.impact += impactDelta;
      citizen.reputation += reputationDelta;
      next.impactEvents.unshift({ id: id("impact"), citizenId: citizen.id, questId: quest.id, amount: impactDelta, scale: quest.expectedImpact, createdAt: now() });
      appendLegacy(next, citizen.id, quest.subnetId, quest.id, `Completed quest: ${quest.title}`, quest.reward, impactDelta, reputationDelta);
      return withAudit(next, "quest.settle", quest.id, quest.title);
    }
    case "creditPulse": {
      assertPositive(action.amount, "Pulse credit amount must be greater than zero.");
      assertText(action.reason, "Pulse credit reason is required.");
      assertInternalPulseReason(action.reason);
      findRequired(next.citizens, action.citizenId, "Citizen was not found.");
      creditPulse(next, "treasury.alpha", action.citizenId, action.amount, action.reason.trim(), null);
      return withAudit(next, "pulse.credit", action.citizenId, `${action.amount} internal Pulse Credits credited`);
    }
    case "flowPulse": {
      assertPositive(action.amount, "Pulse flow amount must be greater than zero.");
      assertText(action.reason, "Pulse flow reason is required.");
      assertInternalPulseReason(action.reason);
      transferPulse(next, action.fromCitizenId, action.toCitizenId, action.amount, action.reason.trim());
      return withAudit(next, "pulse.flow", action.toCitizenId, `${action.amount} internal Pulse Credits flowed`);
    }
    case "publishListing": {
      const seller = findRequired(next.citizens, action.sellerId, "Seller citizen was not found.");
      const title = boundedText(action.title, "Listing title is required.", 100);
      const description = boundedText(action.description, "Listing description is required.", 1200);
      const unit = boundedText(action.unit, "Listing unit is required.", 80);
      const proofRequired = boundedText(action.proofRequired, "Listing proof requirement is required.", 600);
      assertListingCategory(action.category);
      assertPositive(action.price, "Listing price must be greater than zero.");

      const listing: MarketplaceListing = {
        id: id("listing"),
        sellerId: seller.id,
        title,
        category: action.category,
        description,
        price: action.price,
        unit,
        proofRequired,
        status: "Open",
        createdAt: now()
      };
      next.marketplace.unshift(listing);
      appendLegacy(next, seller.id, null, null, `Published marketplace listing: ${listing.title}`, 0, 1, 1);
      return withAudit(next, "market.listing.publish", listing.id, listing.title);
    }
    case "submitFeedback": {
      const citizen = findRequired(next.citizens, action.citizenId, "Citizen was not found.");
      assertFeedbackScope(action.scope);
      const message = boundedText(action.message, "Feedback message is required.", 1400);
      const benefit = boundedText(action.benefit, "Platform benefit explanation is required.", 800);
      const feedback = {
        id: id("feedback"),
        citizenId: citizen.id,
        scope: action.scope,
        message,
        benefit,
        status: "Submitted" as const,
        createdAt: now()
      };
      next.feedback.unshift(feedback);
      return withAudit(next, "feedback.submit", feedback.id, `${citizen.name}: ${feedback.scope}`);
    }
    default:
      return { state, event: null };
  }
}

export function pulseSafetyNotice() {
  return "Pulse Credits are closed-loop software credits for Void: internally priced at 1 USD = 1,000 credits, non-cash, non-redeemable, and not available for external exchange.";
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

function capabilitiesForActor(state: VoidState, actor: VoidActor): Set<VoidCapability> {
  const citizen = findRequired(state.citizens, actor.citizenId, "Actor citizen was not found.");

  if (citizen.status !== "Active") throw new Error("Actor citizen is not active.");

  const capabilities = new Set<VoidCapability>();

  if (citizen.status === "Active") {
    capabilities.add("subnet.create");
    capabilities.add("subnet.join");
    capabilities.add("quest.publish");
    capabilities.add("quest.claim");
    capabilities.add("quest.proof.submit");
    capabilities.add("pulse.flow");
    capabilities.add("market.listing.publish");
    capabilities.add("feedback.submit");
  }

  if (actor.isAdmin && (citizen.titles.includes("Founder") || citizen.titles.includes("Admin"))) {
    capabilities.add("admin.activation.approve");
    capabilities.add("admin.activation.deny");
    capabilities.add("admin.pulse.grant");
    capabilities.add("quest.verify");
  }

  return capabilities;
}

function requireCapability(capabilities: Set<VoidCapability>, capability: VoidCapability) {
  if (!capabilities.has(capability)) throw new Error(`Actor lacks required capability: ${capability}.`);
}

function assertActorOwns(targetCitizenId: string, actorCitizenId: string, message: string) {
  if (targetCitizenId !== actorCitizenId) throw new Error(message);
}

function assertActorIsQuestAssignee(state: VoidState, questId: string, actorCitizenId: string) {
  const quest = findRequired(state.quests, questId, "Quest was not found.");
  if (quest.assigneeId !== actorCitizenId) {
    throw new Error("Only the assigned citizen can submit proof for this quest.");
  }
}

function creditPulse(state: VoidState, source: string, destinationCitizenId: string, amount: number, reason: string, questId: string | null) {
  const citizen = findRequired(state.citizens, destinationCitizenId, "Citizen was not found.");
  citizen.pulse += amount;
  state.ledger.unshift({
    id: id("pulse"),
    source,
    destination: destinationCitizenId,
    amount,
    amountUnits: creditsToUnits(amount).toString(),
    reason,
    flowType: "credit",
    questId,
    createdAt: now()
  });
}

function transferPulse(state: VoidState, fromCitizenId: string, toCitizenId: string, amount: number, reason: string) {
  if (fromCitizenId === toCitizenId) throw new Error("Pulse must flow between two different citizens.");
  const fromCitizen = findRequired(state.citizens, fromCitizenId, "Source citizen was not found.");
  const toCitizen = findRequired(state.citizens, toCitizenId, "Destination citizen was not found.");
  if (fromCitizen.pulse < amount) throw new Error("Source citizen does not have enough internal Pulse Credits.");

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
    source: fromCitizen.id,
    destination: toCitizen.id,
    amount: netAmount,
    amountUnits: fee.netUnits,
    ...sharedSettlement,
    reason,
    flowType: "transfer",
    questId: null,
    createdAt
  });
  state.ledger.unshift({
    id: `${transferId}_out`,
    source: fromCitizen.id,
    destination: fromCitizen.id,
    amount: -amount,
    amountUnits: `-${grossUnits.toString()}`,
    ...sharedSettlement,
    reason: `Sent to ${toCitizen.name}: ${reason}`,
    flowType: "debit",
    questId: null,
    createdAt
  });
  state.ledger.unshift({
    id: `${transferId}_fee`,
    source: fromCitizen.id,
    destination: "vault.pulse.fees",
    amount: fee.fee.total,
    amountUnits: fee.units.totalUnits,
    ...sharedSettlement,
    reason: `6.18% protocol fee: ${reason}`,
    flowType: "credit",
    questId: null,
    createdAt
  });

  appendLegacy(state, fromCitizen.id, null, null, `Sent Pulse to ${toCitizen.name}`, -amount, 0, 0);
  appendLegacy(state, toCitizen.id, null, null, `Received Pulse from ${fromCitizen.name}`, netAmount, 0, 0);
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

function withAudit(state: VoidState, type: string, targetId: string, label: string): VoidApiResult {
  const previous = state.audit[0]?.digest || "GENESIS";
  const event: AuditEvent = {
    id: id("audit"),
    type,
    targetId,
    target: label,
    previous,
    digest: digest(`${previous}|${type}|${targetId}|${label}|${Date.now()}`),
    createdAt: now()
  };
  state.audit.unshift(event);
  return { state, event };
}

function appendLegacy(
  state: VoidState,
  citizenId: string,
  subnetId: string | null,
  questId: string | null,
  action: string,
  pulseDelta: number,
  impactDelta: number,
  reputationDelta: number
) {
  const event: LegacyEvent = { id: id("legacy"), citizenId, subnetId, questId, action, pulseDelta, impactDelta, reputationDelta, createdAt: now() };
  state.legacy.unshift(event);
}

function findRequired<T extends { id: string }>(items: T[], idValue: string | null, message: string): T {
  const item = items.find((entry) => entry.id === idValue);
  if (!item) throw new Error(message);
  return item;
}

function assertText(value: string, message: string) {
  if (!value || !value.trim()) throw new Error(message);
}

function boundedText(value: string, message: string, maxLength: number) {
  assertText(value, message);
  const trimmed = value.trim();
  if (trimmed.length > maxLength) throw new Error(`${message.replace(/\.$/, "")} must be ${maxLength} characters or fewer.`);
  return trimmed;
}

function optionalBoundedText(value: string, maxLength: number) {
  const trimmed = (value || "").trim();
  if (trimmed.length > maxLength) throw new Error(`Text must be ${maxLength} characters or fewer.`);
  return trimmed;
}

function boundedEmail(value: string) {
  const email = boundedText(value, "A valid email is required.", 160).toLowerCase();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error("A valid email is required.");
  return email;
}

function assertPositive(value: number, message: string) {
  if (!Number.isFinite(value) || value <= 0) throw new Error(message);
}

function assertInternalPulseReason(value: string) {
  const forbidden = /\b(cash|redeem|redemption|withdraw|withdrawal|exchange|external wallet|wallet asset|staking|yield|investment|profit|liquidity|token sale)\b/i;
  if (forbidden.test(value)) {
    throw new Error("Pulse reasons must preserve internal, non-cash, non-redeemable alpha accounting language.");
  }
}

function assertCitizenType(value: CitizenType) {
  if (!["Human", "AI Agent", "Machine", "Organization"].includes(value)) {
    throw new Error("Citizen type is not supported.");
  }
}

function assertFeedbackScope(value: FeedbackScope) {
  if (!["Experience", "AI Companion", "Resources", "Governance", "Safety", "Other"].includes(value)) {
    throw new Error("Feedback scope is not supported.");
  }
}

function assertListingCategory(value: ListingCategory) {
  if (!["Compute", "Service", "Training", "Product", "Data", "Model"].includes(value)) {
    throw new Error("Marketplace listing category is not supported.");
  }
}

function addUnique(items: string[], value: string) {
  if (!items.includes(value)) items.push(value);
}

function cloneState(state: VoidState): VoidState {
  return JSON.parse(JSON.stringify(state)) as VoidState;
}

function id(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}_${Date.now().toString(36)}`;
}

function now() {
  return new Date().toISOString();
}

function digest(input: string) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return `VOID-${(hash >>> 0).toString(16).toUpperCase().padStart(8, "0")}`;
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

export type {
  ActivationRequest,
  AuditEvent,
  Citizen,
  CitizenType,
  FeedbackScope,
  ImpactEvent,
  LegacyEvent,
  ListingCategory,
  MarketplaceListing,
  PulseLedgerEvent,
  Quest,
  Subnet,
  VoidState
};
