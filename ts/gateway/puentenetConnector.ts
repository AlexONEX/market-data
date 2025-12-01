import { HttpClient } from "./httpClient";
import { Cashflow } from "../domain/types";
import { CsvWriter } from "../utils/csvWriter";
import * as fs from "fs";

interface PuenteNetCashflow {
  fechaPago: number;
  importeAmortizacion: number;
  importeRenta: number;
  importe: number;
}

interface PuenteNetResponse {
  errores?: string[];
  mapFlujosDTO?: Record<string, PuenteNetCashflow[]>;
}

export class PuenteNetConnector {
  private static readonly BASE_URL = "https://www.puentenet.com/";
  private static readonly CASHFLOW_ENDPOINT =
    "herramientas/flujo-de-fondos/calcular";
  private static readonly CASHFLOW_CSV = "data/cashflows.csv";

  private httpClient: HttpClient;
  private csvWriter: CsvWriter;
  private cache: Map<string, Cashflow[]> = new Map();

  constructor() {
    this.httpClient = new HttpClient({ baseURL: PuenteNetConnector.BASE_URL });
    this.csvWriter = new CsvWriter();
    this.loadCashflowsFromCSV();
  }

  private loadCashflowsFromCSV(): void {
    if (!fs.existsSync(PuenteNetConnector.CASHFLOW_CSV)) {
      return;
    }

    const data = this.csvWriter.readFile(PuenteNetConnector.CASHFLOW_CSV);
    if (data.length === 0) {
      return;
    }

    const headers = data[0] as string[];
    const tickerIdx = headers.indexOf("Ticker");
    const dateIdx = headers.indexOf("PaymentDate");
    const totalIdx = headers.indexOf("TotalPayment");
    const amortIdx = headers.indexOf("Amortization");
    const interestIdx = headers.indexOf("Interest");

    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      if (!Array.isArray(row)) {
        continue;
      }

      const ticker = String(row[tickerIdx] ?? "");

      if (!ticker) continue;

      const cashflow: Cashflow = {
        paymentDate: new Date(String(row[dateIdx] ?? "")),
        totalPayment: Number(row[totalIdx] ?? 0),
        amortization: Number(row[amortIdx] ?? 0),
        interest: Number(row[interestIdx] ?? 0),
      };

      if (!this.cache.has(ticker)) {
        this.cache.set(ticker, []);
      }

      const cfs = this.cache.get(ticker);
      if (cfs) {
        cfs.push(cashflow);
      }
    }
  }

  async getCashflows(
    ticker: string,
    nominalValue: number = 100
  ): Promise<Cashflow[]> {
    const cached = this.cache.get(ticker);
    if (cached) {
      return cached;
    }

    const rawData = await this.fetchFromPuenteNet(ticker, nominalValue);
    const parsed = this.parseCashflows(rawData);

    if (parsed.length > 0) {
      this.cache.set(ticker, parsed);
      this.saveCashflowsToCSV(ticker, parsed);
    }

    return parsed;
  }

  private async fetchFromPuenteNet(
    ticker: string,
    nominalValue: number
  ): Promise<PuenteNetResponse | null> {
    try {
      const url = PuenteNetConnector.CASHFLOW_ENDPOINT;
      const payload = { [`BONO_${ticker}`]: String(nominalValue) };
      const headers = {
        "Content-Type": "application/json",
        Referer:
          PuenteNetConnector.BASE_URL +
          PuenteNetConnector.CASHFLOW_ENDPOINT.split("/calcular")[0],
      };

      const response = await this.httpClient.post<PuenteNetResponse>(url);
      return response;
    } catch {
      return null;
    }
  }

  private parseCashflows(rawData: PuenteNetResponse | null): Cashflow[] {
    if (!rawData) {
      return [];
    }

    if (rawData.errores && rawData.errores.length > 0) {
      return [];
    }

    const mapFlujosDTO = rawData.mapFlujosDTO;
    if (!mapFlujosDTO) {
      return [];
    }

    let targetCashflows: PuenteNetCashflow[] | undefined;

    for (const key of ["USD", "ARS", "PESOS"]) {
      if (mapFlujosDTO[key]) {
        targetCashflows = mapFlujosDTO[key];
        break;
      }
    }

    if (!targetCashflows) {
      const firstKey = Object.keys(mapFlujosDTO)[0];
      if (firstKey) {
        targetCashflows = mapFlujosDTO[firstKey];
      }
    }

    if (!targetCashflows || !Array.isArray(targetCashflows)) {
      return [];
    }

    const parsed: Cashflow[] = [];

    for (const cf of targetCashflows) {
      const paymentDate = new Date(cf.fechaPago);
      const totalPayment = Number(cf.importe ?? 0);

      if (totalPayment > 0) {
        parsed.push({
          paymentDate,
          totalPayment,
          amortization: Number(cf.importeAmortizacion ?? 0),
          interest: Number(cf.importeRenta ?? 0),
        });
      }
    }

    parsed.sort((a, b) => a.paymentDate.getTime() - b.paymentDate.getTime());

    return parsed;
  }

  private saveCashflowsToCSV(ticker: string, cashflows: Cashflow[]): void {
    const fileExists = fs.existsSync(PuenteNetConnector.CASHFLOW_CSV);
    const data: unknown[][] = [];

    if (!fileExists) {
      data.push([
        "Ticker",
        "PaymentDate",
        "TotalPayment",
        "Amortization",
        "Interest",
      ]);
    } else {
      const existing = this.csvWriter.readFile(
        PuenteNetConnector.CASHFLOW_CSV
      );
      data.push(...existing);
    }

    for (const cf of cashflows) {
      data.push([
        ticker,
        cf.paymentDate.toISOString().split("T")[0],
        cf.totalPayment,
        cf.amortization,
        cf.interest,
      ]);
    }

    this.csvWriter.writeFile(PuenteNetConnector.CASHFLOW_CSV, data);
  }
}
