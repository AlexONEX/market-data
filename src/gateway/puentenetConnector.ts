import { DataSource } from "../domain";
import { getLogger } from "../utils/logger";
import { HttpClient } from "./httpClient";

const logger = getLogger();

export interface CashFlow {
  date: string; // ISO date string
  amortization: number;
  interest: number;
  totalPayment: number;
}

export interface PuenteNetCashFlowResponse {
  ticker: string;
  cashflows: CashFlow[];
}

/**
 * Connector for PuenteNet API - Argentine bond cash flows
 * Fetches cash flow schedules for Argentine bonds
 */
export class PuenteNetConnector {
  readonly name = "puentenet";
  private readonly httpClient: HttpClient;
  private readonly baseURL = "https://www.puentenet.com";
  private readonly cashflowEndpoint = "herramientas/flujo-de-fondos/calcular";
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

  constructor() {
    this.httpClient = new HttpClient({
      baseURL: this.baseURL,
      timeout: 15000,
      retryAttempts: 1,
    });
  }

  get isHealthy(): boolean {
    return this.isHealthyFlag;
  }

  get lastError(): Error | undefined {
    return this.lastErrorValue;
  }

  get lastErrorTime(): Date | undefined {
    return this.lastErrorTimeValue;
  }

  markHealthy(): void {
    this.isHealthyFlag = true;
    this.lastErrorValue = undefined;
    this.lastErrorTimeValue = undefined;
  }

  markUnhealthy(error: Error): void {
    this.isHealthyFlag = false;
    this.lastErrorValue = error;
    this.lastErrorTimeValue = new Date();
  }

  /**
   * Fetch cash flows for a bond ticker
   */
  async getCashflows(ticker: string, nominalValue: number = 100): Promise<CashFlow[]> {
    try {
      const payload = { [`BONO_${ticker}`]: String(nominalValue) };

      const response = await this.httpClient.post<unknown>(
        `/${this.cashflowEndpoint}`,
        DataSource.Data912,
        payload,
      );

      const cashflows = this.parseCashflows(response.data, ticker);
      this.markHealthy();

      return cashflows;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      logger.error({ ticker, error: err.message }, "Failed to fetch cash flows from PuenteNet");
      throw err;
    }
  }

  /**
   * Parse cash flows from PuenteNet response
   */
  private parseCashflows(rawData: unknown, ticker: string): CashFlow[] {
    if (!rawData || typeof rawData !== "object") {
      logger.warn({ ticker }, "Invalid or empty PuenteNet response");
      return [];
    }

    const data = rawData as Record<string, unknown>;

    // Check for errors in response
    const errors = data["errores"];
    if (Array.isArray(errors) && errors.length > 0) {
      errors.forEach((error) => {
        logger.warn({ ticker, error }, "PuenteNet API error");
      });
      return [];
    }

    // Extract cash flows from response structure
    const mapFlujosDTO = data["mapFlujosDTO"];
    if (!mapFlujosDTO || typeof mapFlujosDTO !== "object") {
      logger.warn({ ticker }, "No mapFlujosDTO in PuenteNet response");
      return [];
    }

    // Try to find cash flows in common currency keys
    let targetCashflows: unknown[] | null = null;
    for (const currencyKey of ["USD", "ARS", "PESOS"]) {
      const cf = (mapFlujosDTO as Record<string, unknown>)[currencyKey];
      if (Array.isArray(cf)) {
        targetCashflows = cf;
        break;
      }
    }

    // If not found, try the first available currency
    if (!targetCashflows) {
      const keys = Object.keys(mapFlujosDTO as Record<string, unknown>);
      if (keys.length > 0) {
        const firstKey = keys[0];
        if (firstKey) {
          const cf = (mapFlujosDTO as Record<string, unknown>)[firstKey];
          if (Array.isArray(cf)) {
            targetCashflows = cf;
          }
        }
      }
    }

    if (!targetCashflows) {
      logger.warn({ ticker }, "No cash flows found in PuenteNet response");
      return [];
    }

    // Parse individual cash flows
    const parsed: CashFlow[] = [];
    for (const cf of targetCashflows) {
      if (typeof cf !== "object" || !cf) continue;

      try {
        const cfData = cf as Record<string, unknown>;
        const paymentDateTimestamp = cfData["fechaPago"] as number | undefined;

        if (paymentDateTimestamp === undefined || paymentDateTimestamp === null) {
          logger.debug({ ticker }, "Cash flow without payment date");
          continue;
        }

        const paymentDate = new Date(paymentDateTimestamp).toISOString().split("T")[0] || "";
        const amortization = Number(cfData["importeAmortizacion"] ?? 0);
        const interest = Number(cfData["importeRenta"] ?? 0);
        const totalPayment = Number(cfData["importe"] ?? 0);

        if (totalPayment > 0) {
          parsed.push({
            date: paymentDate,
            amortization,
            interest,
            totalPayment,
          });
        }
      } catch (error) {
        logger.debug(
          { ticker, error: error instanceof Error ? error.message : String(error) },
          "Error parsing cash flow",
        );
        continue;
      }
    }

    // Sort by date
    parsed.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    logger.info({ ticker, count: parsed.length }, "Successfully parsed PuenteNet cash flows");
    return parsed;
  }
}
