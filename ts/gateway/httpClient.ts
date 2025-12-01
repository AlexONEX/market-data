import axios, { AxiosInstance, AxiosError } from "axios";

export interface HttpClientConfig {
  baseURL?: string;
  timeout?: number;
}

export interface HttpResponse<T> {
  status: number;
  data: T;
  headers: Record<string, string>;
}

export class HttpClient {
  private readonly client: AxiosInstance;
  private readonly timeout: number;

  constructor(config: HttpClientConfig = {}) {
    this.timeout = config.timeout ?? 10000;
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: this.timeout,
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });
  }

  async get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
    try {
      const response = await this.client.get<T>(url, { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error, `GET ${url}`);
    }
  }

  async post<T>(url: string, data?: unknown): Promise<T> {
    try {
      const response = await this.client.post<T>(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error, `POST ${url}`);
    }
  }

  private handleError(error: unknown, description: string): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;
      if (axiosError.response) {
        return new Error(`HTTP ${axiosError.response.status}: ${description}`);
      }
      if (axiosError.request) {
        return new Error(`No response from server: ${description}`);
      }
    }

    if (error instanceof Error) {
      return error;
    }

    return new Error(`Unknown error: ${description}`);
  }
}
