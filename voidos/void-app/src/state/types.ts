export type CitizenType = "Human" | "AI Agent" | "Machine" | "Organization";
export type RequestStatus = "Pending" | "Approved" | "Denied";
export type QuestStatus = "Open" | "Claimed" | "Submitted" | "Rejected" | "Settled";
export type FeedbackStatus = "Submitted" | "Beneficial" | "Deferred" | "Rejected";
export type FeedbackScope = "Experience" | "AI Companion" | "Resources" | "Governance" | "Safety" | "Other";
export type PulseVaultKey = "ubi" | "infrastructure" | "operating";
export type PulseVaults = Record<PulseVaultKey, number>;
export type ListingCategory = "Compute" | "Service" | "Training" | "Product" | "Data" | "Model";
export type ListingStatus = "Open" | "Paused" | "Fulfilled";

export type AICompanionProfile = {
  name: string;
  mode: "Local Companion" | "Operator-Supervised Agent" | "Organization Steward";
  onboardingStage: "New" | "Learning" | "Contributing" | "Trusted";
  directives: string[];
  learningFocus: string[];
};

export type OnboardingPlan = {
  stage: "Orientation" | "First Contribution" | "Reputation Building" | "Marketplace Ready";
  nextActions: string[];
  suggestedQuestClass: string;
  suggestedListingCategory: ListingCategory;
  createdAt: string;
};

export type ActivationRequest = {
  id: string;
  name: string;
  email: string;
  type: CitizenType;
  operator: string;
  purpose: string;
  status: RequestStatus;
  createdAt: string;
};

export type Citizen = {
  id: string;
  name: string;
  email: string;
  type: CitizenType;
  operator: string;
  status: "Active";
  pulse: number;
  impact: number;
  reputation: number;
  titles: string[];
  subnets: string[];
  aiCompanion: AICompanionProfile;
  onboardingPlan: OnboardingPlan;
  createdAt: string;
};

export type Subnet = {
  id: string;
  name: string;
  focus: string;
  charter: string;
  founderId: string;
  treasury: number;
  members: string[];
  createdAt: string;
};

export type Quest = {
  id: string;
  subnetId: string;
  issuerId: string;
  title: string;
  class: string;
  reward: number;
  expectedImpact: number;
  proofRequired: string;
  status: QuestStatus;
  assigneeId: string | null;
  submission: { proof: string; submittedAt: string } | null;
  createdAt: string;
};

export type PulseLedgerEvent = {
  id: string;
  source: string;
  destination: string;
  amount: number;
  amountUnits?: string;
  grossAmount?: number;
  grossUnits?: string;
  netAmount?: number;
  netUnits?: string;
  feeAmount?: number;
  feeUnits?: string;
  feeSplit?: PulseVaults;
  feeSplitUnits?: Record<PulseVaultKey, string>;
  reason: string;
  flowType: "credit" | "debit" | "transfer";
  questId: string | null;
  createdAt: string;
};

export type MarketplaceListing = {
  id: string;
  sellerId: string;
  title: string;
  category: ListingCategory;
  description: string;
  price: number;
  unit: string;
  proofRequired: string;
  status: ListingStatus;
  createdAt: string;
};

export type ImpactEvent = {
  id: string;
  citizenId: string;
  questId: string;
  amount: number;
  scale: number;
  createdAt: string;
};

export type LegacyEvent = {
  id: string;
  citizenId: string;
  subnetId: string | null;
  questId: string | null;
  action: string;
  pulseDelta: number;
  impactDelta: number;
  reputationDelta: number;
  createdAt: string;
};

export type AuditEvent = {
  id: string;
  type: string;
  targetId: string;
  target: string;
  previous: string;
  digest: string;
  createdAt: string;
};

export type FeedbackRecord = {
  id: string;
  citizenId: string;
  scope: FeedbackScope;
  message: string;
  benefit: string;
  status: FeedbackStatus;
  createdAt: string;
};

export type VoidState = {
  currentCitizenId: string;
  activationRequests: ActivationRequest[];
  citizens: Citizen[];
  subnets: Subnet[];
  quests: Quest[];
  marketplace: MarketplaceListing[];
  ledger: PulseLedgerEvent[];
  pulseVaults: PulseVaults;
  impactEvents: ImpactEvent[];
  legacy: LegacyEvent[];
  audit: AuditEvent[];
  feedback: FeedbackRecord[];
  mesh?: {
    mass: number;
    energy: number;
    entropy: number;
    cycle: number;
  };
};

export type VoidApiResponse = {
  ok: boolean;
  state: VoidState;
  message?: string;
};
