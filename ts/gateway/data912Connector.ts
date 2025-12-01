import { HttpClient } from "./httpClient";

export interface Instrument {
  symbol: string;
  pxBid?: number;
  pxAsk?: number;
  c?: number;
  [key: string]: unknown;
}

export class Data912Connector {
  private static readonly URL_BONDS = "https://data912.com/live/arg_bonds";
  private static readonly URL_NOTES = "https://data912.com/live/arg_notes";

  private httpClient: HttpClient;

  constructor() {
    this.httpClient = new HttpClient();
  }

  async fetchInstruments(
    url: string
  ): Promise<Record<string, Instrument>> {
    try {
      const data = await this.httpClient.get<Instrument[]>(url);

      if (!Array.isArray(data)) {
        return {};
      }

      const result: Record<string, Instrument> = {};
      for (const instrument of data) {
        const symbol = instrument.symbol as string;
        if (symbol) {
          result[symbol] = instrument;
        }
      }
      return result;
    } catch {
      return {};
    }
  }

  async getAllInstruments(): Promise<Record<string, Instrument>> {
    const [bonds, notes] = await Promise.all([
      this.fetchInstruments(Data912Connector.URL_BONDS),
      this.fetchInstruments(Data912Connector.URL_NOTES),
    ]);

    return { ...bonds, ...notes };
  }

  getPrice(instrument: Instrument): number {
    const bid = Number(instrument.pxBid ?? 0);
    const ask = Number(instrument.pxAsk ?? 0);
    const close = Number(instrument.c ?? 0);

    if (close > 0) return close;
    if (ask > 0) return ask;
    return bid;
  }
}
