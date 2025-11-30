import Decimal from "decimal.js";

import { Cashflow, TIRCalculationError } from "./types";

interface TimedCashflow {
  readonly daysSinceStart: number;
  readonly amount: number;
}

function createTimedCashflows(
  cashflows: readonly Cashflow[],
  settlementDate: Date,
): TimedCashflow[] {
  return cashflows.map((cf) => ({
    daysSinceStart: Math.floor(
      (cf.paymentDate.getTime() - settlementDate.getTime()) / (1000 * 60 * 60 * 24),
    ),
    amount: cf.totalPayment,
  }));
}

function calculateNetPresentValue(
  timedCashflows: readonly TimedCashflow[],
  currentPrice: number,
  annualRate: Decimal,
): Decimal {
  let npv = new Decimal(-currentPrice);

  for (const cf of timedCashflows) {
    const exponent = new Decimal(cf.daysSinceStart).dividedBy(365);
    const discountFactor = annualRate.plus(1).pow(exponent);
    const presentValue = new Decimal(cf.amount).dividedBy(discountFactor);
    npv = npv.plus(presentValue);
  }

  return npv;
}

export function calculateTIRNewtonRaphson(
  cashflows: readonly Cashflow[],
  currentPrice: number,
  settlementDate: Date,
): number {
  if (cashflows.length === 0) {
    throw new TIRCalculationError("Cashflows array is empty");
  }

  if (currentPrice <= 0) {
    throw new TIRCalculationError("Current price must be positive", { currentPrice });
  }

  const timedCashflows = createTimedCashflows(cashflows, settlementDate);

  Decimal.set({ precision: 50, rounding: 1 });

  // Use bisection method for robustness
  let low = new Decimal(-0.9); // -90% yield (bond in distress)
  let high = new Decimal(2.0); // 200% yield (extremely high return)
  const maxIterations = 100;
  const tolerance = new Decimal("1e-8");

  // Verify that NPV has opposite signs at boundaries
  let npvLow = calculateNetPresentValue(timedCashflows, currentPrice, low);
  let npvHigh = calculateNetPresentValue(timedCashflows, currentPrice, high);

  if (
    (npvLow.greaterThan(0) && npvHigh.greaterThan(0)) ||
    (npvLow.lessThan(0) && npvHigh.lessThan(0))
  ) {
    throw new TIRCalculationError(
      "NPV does not change sign in range [-90%, 200%], cannot find TIR",
      { npvAtLow: npvLow.toString(), npvAtHigh: npvHigh.toString() },
    );
  }

  for (let iteration = 0; iteration < maxIterations; iteration++) {
    const mid = low.plus(high).dividedBy(2);
    const npvMid = calculateNetPresentValue(timedCashflows, currentPrice, mid);

    if (npvMid.absoluteValue().lessThan(tolerance)) {
      return Number(mid.toFixed(10));
    }

    // Choose which half to keep based on sign change
    if (
      (npvLow.lessThan(0) && npvMid.greaterThan(0)) ||
      (npvLow.greaterThan(0) && npvMid.lessThan(0))
    ) {
      high = mid;
      npvHigh = npvMid;
    } else {
      low = mid;
      npvLow = npvMid;
    }

    const difference = high.minus(low).absoluteValue();
    if (difference.lessThan(tolerance)) {
      const result = high.plus(low).dividedBy(2).toFixed(10);
      return Number(result);
    }
  }

  throw new TIRCalculationError("Bisection did not converge within max iterations", {
    maxIterations,
    finalLow: low.toString(),
    finalHigh: high.toString(),
  });
}

export function calculateMonthlyRate(annualRate: number): number {
  // TEM = (1 + TIR)^(1/12) - 1
  const oneAnnualRate = 1 + annualRate;
  const monthlyRate = Math.pow(oneAnnualRate, 1 / 12) - 1;
  return monthlyRate;
}

export function calculateYieldCurvePoint(maturityDays: number, annualRate: number): number {
  const maturityYears = maturityDays / 365;
  return Math.pow(1 + annualRate, maturityYears) - 1;
}
