import { Cashflow, DataSource, ValidationError } from "./types";

export function validateTicker(ticker: string): void {
  if (!ticker || ticker.trim().length === 0) {
    throw new ValidationError("Ticker cannot be empty");
  }

  if (ticker.length > 10) {
    throw new ValidationError("Ticker cannot exceed 10 characters", {
      ticker,
      length: ticker.length,
    });
  }

  if (!/^[A-Z0-9]{1,10}$/.test(ticker)) {
    throw new ValidationError("Ticker must contain only uppercase letters and numbers", {
      ticker,
    });
  }
}

export function validatePrice(price: number): void {
  if (typeof price !== "number" || Number.isNaN(price)) {
    throw new ValidationError("Price must be a valid number", { price });
  }

  if (price < 0) {
    throw new ValidationError("Price cannot be negative", { price });
  }

  if (price === 0) {
    throw new ValidationError("Price cannot be zero", { price });
  }

  if (!Number.isFinite(price)) {
    throw new ValidationError("Price must be finite", { price });
  }
}

export function validateDate(date: Date | string): Date {
  let dateObj: Date;

  if (typeof date === "string") {
    dateObj = new Date(date);
  } else if (date instanceof Date) {
    dateObj = date;
  } else {
    throw new ValidationError("Date must be a Date object or ISO string", { date });
  }

  if (Number.isNaN(dateObj.getTime())) {
    throw new ValidationError("Invalid date", { date });
  }

  return dateObj;
}

export function validateCashflows(cashflows: readonly unknown[]): Cashflow[] {
  if (!Array.isArray(cashflows) || cashflows.length === 0) {
    throw new ValidationError("Cashflows must be a non-empty array", {
      cashflowsLength: cashflows?.length,
    });
  }

  const validatedCashflows: Cashflow[] = [];

  for (const cf of cashflows) {
    if (typeof cf !== "object" || cf === null) {
      throw new ValidationError("Each cashflow must be an object", { cashflow: cf });
    }

    const cashflow = cf as Record<string, unknown>;

    const paymentDate = validateDate(cashflow["paymentDate"] as string | Date);
    const totalPayment = cashflow["totalPayment"] as number;
    const amortization = cashflow["amortization"] as number;
    const interest = cashflow["interest"] as number;

    if (typeof totalPayment !== "number" || Number.isNaN(totalPayment)) {
      throw new ValidationError("Cashflow totalPayment must be a number", {
        totalPayment,
      });
    }

    if (typeof amortization !== "number" || Number.isNaN(amortization)) {
      throw new ValidationError("Cashflow amortization must be a number", {
        amortization,
      });
    }

    if (typeof interest !== "number" || Number.isNaN(interest)) {
      throw new ValidationError("Cashflow interest must be a number", {
        interest,
      });
    }

    validatedCashflows.push({
      paymentDate,
      totalPayment,
      amortization,
      interest,
    });
  }

  return validatedCashflows;
}

export function validateDataSource(source: string): DataSource {
  const validSources = Object.values(DataSource);

  if (!validSources.includes(source as DataSource)) {
    throw new ValidationError(`Invalid data source: ${source}`, {
      source,
      validSources,
    });
  }

  return source as DataSource;
}

export function validatePercentage(value: number): void {
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new ValidationError("Percentage must be a valid number", { value });
  }

  if (value < -100 || value > 100) {
    throw new ValidationError("Percentage must be between -100 and 100", {
      value,
    });
  }
}
