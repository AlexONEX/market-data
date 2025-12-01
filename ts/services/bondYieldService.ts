import { calculateTir, calculateMacaulayDuration, convertTiraToTem } from "../domain/financialMath";
import { TIRResult, Cashflow } from "../domain/types";
import { PuenteNetConnector } from "../gateway/puentenetConnector";
import { Data912Connector } from "../gateway/data912Connector";

export class BondYieldService {
  private puenteNetConnector: PuenteNetConnector;
  private data912Connector: Data912Connector;

  constructor() {
    this.puenteNetConnector = new PuenteNetConnector();
    this.data912Connector = new Data912Connector();
  }

  async calculateBondYield(
    ticker: string,
    settlementDate: Date
  ): Promise<TIRResult | null> {
    const instruments = await this.data912Connector.getAllInstruments();
    const instrument = instruments[ticker];

    if (!instrument) {
      return null;
    }

    const price = this.data912Connector.getPrice(instrument);
    if (price <= 0) {
      return null;
    }

    const cashflows = await this.puenteNetConnector.getCashflows(ticker);
    if (cashflows.length === 0) {
      return null;
    }

    const tir = calculateTir(cashflows, price, settlementDate);
    if (tir === null) {
      return null;
    }

    const duration = calculateMacaulayDuration(cashflows, tir, settlementDate);
    const maturityDate = cashflows[cashflows.length - 1]?.paymentDate;

    if (!maturityDate) {
      return null;
    }

    return {
      ticker,
      tir,
      price,
      maturityDate,
      duration: duration ?? undefined,
    };
  }

  async calculateMultipleBondYields(
    tickers: string[],
    settlementDate: Date
  ): Promise<TIRResult[]> {
    const results: TIRResult[] = [];

    for (const ticker of tickers) {
      const result = await this.calculateBondYield(ticker, settlementDate);
      if (result) {
        results.push(result);
      }
    }

    return results;
  }

  calculateMonthlyRate(tir: number): number {
    return convertTiraToTem(tir);
  }
}
