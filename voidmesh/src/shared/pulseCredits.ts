export const PULSE_DECIMALS = 18;
export const PULSE_UNITS_PER_CREDIT = 10n ** BigInt(PULSE_DECIMALS);
export const PULSE_CREDITS_PER_USD = 1000;
export const PULSE_UNIT_LABEL = "Pulse Credit";

const FEE_DENOMINATOR = 10000n;
export const PULSE_FEE_BPS = {
  ubi: 318n,
  infrastructure: 200n,
  operating: 100n
} as const;
export const PULSE_TOTAL_FEE_BPS = PULSE_FEE_BPS.ubi + PULSE_FEE_BPS.infrastructure + PULSE_FEE_BPS.operating;
export const PULSE_TOTAL_FEE_PERCENT = "6.18%";

export type PulseFeeSplit = {
  ubi: number;
  infrastructure: number;
  operating: number;
  total: number;
};

export type PulseUnitFeeSplit = {
  ubiUnits: string;
  infrastructureUnits: string;
  operatingUnits: string;
  totalUnits: string;
};

export function creditsToUnits(value: number | string): bigint {
  const text = String(value).trim();
  if (!/^\d+(\.\d{1,18})?$/.test(text)) {
    throw new Error("Pulse Credit amount must be a positive number with up to 18 decimal places.");
  }

  const [whole, fraction = ""] = text.split(".");
  const paddedFraction = fraction.padEnd(PULSE_DECIMALS, "0");
  return BigInt(whole) * PULSE_UNITS_PER_CREDIT + BigInt(paddedFraction || "0");
}

export function unitsToCredits(units: bigint | string): number {
  return Number(formatUnits(units, 6));
}

export function formatPulseCredits(value: number | string | bigint) {
  if (typeof value === "bigint") {
    return trimDecimal(formatUnits(value, 6));
  }

  return trimDecimal(Number(value).toLocaleString("en-US", {
    maximumFractionDigits: 6
  }));
}

export function pulseCreditsToUsd(credits: number) {
  return credits / PULSE_CREDITS_PER_USD;
}

export function usdToPulseCredits(usd: number) {
  return usd * PULSE_CREDITS_PER_USD;
}

export function calculatePulseFeeUnits(grossUnits: bigint): {
  fee: PulseFeeSplit;
  units: PulseUnitFeeSplit;
  netUnits: string;
} {
  const ubiUnits = grossUnits * PULSE_FEE_BPS.ubi / FEE_DENOMINATOR;
  const infrastructureUnits = grossUnits * PULSE_FEE_BPS.infrastructure / FEE_DENOMINATOR;
  const operatingUnits = grossUnits * PULSE_FEE_BPS.operating / FEE_DENOMINATOR;
  const totalUnits = ubiUnits + infrastructureUnits + operatingUnits;
  const netUnits = grossUnits - totalUnits;

  return {
    fee: {
      ubi: unitsToCredits(ubiUnits),
      infrastructure: unitsToCredits(infrastructureUnits),
      operating: unitsToCredits(operatingUnits),
      total: unitsToCredits(totalUnits)
    },
    units: {
      ubiUnits: ubiUnits.toString(),
      infrastructureUnits: infrastructureUnits.toString(),
      operatingUnits: operatingUnits.toString(),
      totalUnits: totalUnits.toString()
    },
    netUnits: netUnits.toString()
  };
}

function formatUnits(value: bigint | string, precision: number) {
  const units = typeof value === "bigint" ? value : BigInt(value);
  const whole = units / PULSE_UNITS_PER_CREDIT;
  const fraction = units % PULSE_UNITS_PER_CREDIT;
  if (precision <= 0 || fraction === 0n) return whole.toString();

  const fractionText = fraction.toString().padStart(PULSE_DECIMALS, "0").slice(0, precision);
  return `${whole}.${fractionText}`;
}

function trimDecimal(text: string) {
  return text.replace(/(\.\d*?)0+$/u, "$1").replace(/\.$/u, "");
}
