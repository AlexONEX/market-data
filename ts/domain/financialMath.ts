import { Cashflow } from "./types";

export function calculateTir(
  cashflows: readonly Cashflow[],
  price: number,
  settlementDate: Date
): number | null {
  if (cashflows.length === 0 || price <= 0) {
    return null;
  }

  const futureCashflows = cashflows.filter((cf) => cf.paymentDate > settlementDate);

  if (futureCashflows.length === 0) {
    return null;
  }

  const dates = futureCashflows.map((cf) => cf.paymentDate);
  const amounts = futureCashflows.map((cf) => cf.totalPayment);

  const npv = (rate: number): number => {
    if (1.0 + rate <= 0) return NaN;
    let totalNpv = 0;
    for (let i = 0; i < dates.length; i++) {
      const date = dates[i];
      const amount = amounts[i];
      if (date === undefined || amount === undefined) {
        return NaN;
      }
      const days = (date.getTime() - settlementDate.getTime()) / (1000 * 86400);
      const exponent = days / 365.0;
      const denominator = 1.0 + rate;
      if (denominator === 0) return NaN;
      totalNpv += amount / Math.pow(denominator, exponent);
    }
    return totalNpv - price;
  };

  const dNpv = (rate: number): number => {
    if (1.0 + rate <= 0) return NaN;
    let totalDNpv = 0;
    for (let i = 0; i < dates.length; i++) {
      const date = dates[i];
      const amount = amounts[i];
      if (date === undefined || amount === undefined) {
        return NaN;
      }
      const days = (date.getTime() - settlementDate.getTime()) / (1000 * 86400);
      const exponent = days / 365.0;
      const denominator = 1.0 + rate;
      if (denominator === 0) return NaN;
      totalDNpv -=
        (amount * exponent) / Math.pow(denominator, exponent + 1.0);
    }
    return totalDNpv;
  };

  let guess = 0.1;
  for (let i = 0; i < 100; i++) {
    const npvVal = npv(guess);
    const dNpvVal = dNpv(guess);

    if (isNaN(npvVal) || isNaN(dNpvVal)) {
      return null;
    }

    if (Math.abs(npvVal) < 1e-9) {
      return guess;
    }

    if (dNpvVal === 0) {
      return null;
    }

    const newGuess = guess - npvVal / dNpvVal;
    guess = newGuess;
  }

  return null;
}

export function calculateMacaulayDuration(
  cashflows: readonly Cashflow[],
  tir: number,
  settlementDate: Date
): number | null {
  if (cashflows.length === 0 || tir === null) {
    return null;
  }

  let presentValueSum = 0;
  let weightedTimeSum = 0;

  for (const cf of cashflows) {
    if (cf.paymentDate > settlementDate) {
      const timeToYears =
        (cf.paymentDate.getTime() - settlementDate.getTime()) /
        (1000 * 86400 * 365.0);

      if (timeToYears <= 0) continue;

      const discountFactor = Math.pow(1.0 + tir, timeToYears);
      const pvCashflow = cf.totalPayment / discountFactor;
      presentValueSum += pvCashflow;
      weightedTimeSum += pvCashflow * timeToYears;
    }
  }

  if (presentValueSum === 0) {
    return null;
  }

  return weightedTimeSum / presentValueSum;
}

export function convertTiraToTem(tiraAnnual: number): number {
  if (tiraAnnual <= -1) return -1;
  return Math.pow(1 + tiraAnnual, 1 / 12) - 1;
}

export function convertTemToTea(tem: number): number {
  return Math.pow(1 + tem, 12) - 1;
}

export function convertTemToTna(tem: number): number {
  return tem * 12;
}
