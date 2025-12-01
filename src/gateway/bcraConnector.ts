import { DataSource } from "../domain";
import { getLogger } from "../utils/logger";
import { HttpClient } from "./httpClient";

const logger = getLogger();

export interface BCRADataPoint {
  fecha: string;
  valor: number;
}

export interface BCRASeries {
  variable_id: number;
  series: BCRADataPoint[];
}

/**
 * Connector for BCRA (Banco Central de la República Argentina) API
 * Fetches Argentine economic and monetary statistics
 */
export class BCRAConnector {
  readonly name = "bcra";
  private readonly httpClient: HttpClient;
  private readonly baseURL = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias";
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

  constructor() {
    this.httpClient = new HttpClient({
      baseURL: this.baseURL,
      timeout: 10000,
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
   * Fetch data for a specific BCRA variable
   * Variable IDs:
   * - 1: Tasa de política monetaria
   * - 7: Tasa de interés de plazo fijo en ARS
   * - 25: Tasa de cambio oficial de compra
   * - 26: Tasa de cambio oficial de venta
   * And many more...
   */
  async getSeriesData(variableId: number): Promise<BCRADataPoint[]> {
    try {
      const url = `/${variableId}`;
      const response = await this.httpClient.get<{ results: BCRADataPoint[] }>(
        url,
        DataSource.BCRA,
      );

      if (!response.data || !response.data.results) {
        logger.warn({ variableId }, "No series data in BCRA response");
        this.markHealthy();
        return [];
      }

      const dataPoints = response.data.results;

      // Parse dates and values
      const parsed = dataPoints
        .filter((point) => point.fecha && point.valor !== null && point.valor !== undefined)
        .map((point) => ({
          fecha: point.fecha,
          valor: typeof point.valor === "string" ? Number.parseFloat(point.valor) : point.valor,
        }))
        .filter((point) => !Number.isNaN(point.valor));

      this.markHealthy();

      logger.info({ variableId, count: parsed.length }, "Successfully fetched BCRA series data");
      return parsed;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      logger.error({ variableId, error: err.message }, "Failed to fetch BCRA series data");
      throw err;
    }
  }

  /**
   * Fetch multiple series at once
   */
  async getMultipleSeries(variableIds: number[]): Promise<Record<number, BCRADataPoint[]>> {
    const results: Record<number, BCRADataPoint[]> = {};

    for (const variableId of variableIds) {
      try {
        results[variableId] = await this.getSeriesData(variableId);
      } catch (error) {
        logger.warn(
          { variableId, error: error instanceof Error ? error.message : String(error) },
          "Failed to fetch individual series",
        );
        results[variableId] = [];
      }
    }

    return results;
  }

  /**
   * Common BCRA variables helper
   */
  static readonly CommonVariables = {
    MONETARY_POLICY_RATE: 1,
    LENDING_RATE: 7,
    FIXED_TERM_RATE_ARS: 72,
    EXCHANGE_RATE_BUY: 25,
    EXCHANGE_RATE_SELL: 26,
    DOLLAR_BLUE_BUY: 192,
    DOLLAR_BLUE_SELL: 193,
    CENTRAL_BANK_RESERVES: 14,
    MONETARY_BASE: 27,
    CPI_INFLATION: 110,
  };
}
