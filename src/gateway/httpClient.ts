import axios, { AxiosInstance, AxiosError } from "axios";

import { DataFetchError, DataSource } from "../domain";
import { HttpClientConfig, HttpResponse } from "./types";

export class HttpClient {
  private readonly axiosInstance: AxiosInstance;
  private readonly config: Required<HttpClientConfig>;

  constructor(config: HttpClientConfig = {}) {
    this.config = {
      baseURL: config.baseURL ?? "",
      timeout: config.timeout ?? 30000,
      retryAttempts: config.retryAttempts ?? 3,
      retryDelay: config.retryDelay ?? 1000,
    };

    this.axiosInstance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
      },
    });
  }

  async get<T>(
    url: string,
    source: DataSource,
    params?: Record<string, unknown>,
  ): Promise<HttpResponse<T>> {
    return this.requestWithRetry<T>(
      async () => this.axiosInstance.get<T>(url, { params }),
      source,
      `GET ${url}`,
    );
  }

  async post<T>(url: string, source: DataSource, data?: unknown): Promise<HttpResponse<T>> {
    return this.requestWithRetry<T>(
      async () => this.axiosInstance.post<T>(url, data),
      source,
      `POST ${url}`,
    );
  }

  private async requestWithRetry<T>(
    request: () => Promise<{ status: number; data: T; headers: unknown }>,
    source: DataSource,
    description: string,
  ): Promise<HttpResponse<T>> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const response = await request();
        return {
          status: response.status,
          data: response.data,
          headers: this.normalizeHeaders(response.headers),
        };
      } catch (error) {
        lastError = this.handleError(error, description);

        if (attempt < this.config.retryAttempts) {
          const delayMs = this.config.retryDelay * attempt;
          await new Promise((resolve) => setTimeout(resolve, delayMs));
        }
      }
    }

    throw new DataFetchError(
      source,
      `Failed after ${this.config.retryAttempts} attempts: ${lastError?.message ?? "Unknown error"}`,
      {
        url: description,
        attempts: this.config.retryAttempts,
        originalError: lastError?.message,
      },
    );
  }

  private normalizeHeaders(headers: unknown): Record<string, string> {
    if (!headers || typeof headers !== "object") {
      return {};
    }

    const result: Record<string, string> = {};
    for (const [key, value] of Object.entries(headers)) {
      if (typeof value === "string") {
        result[key] = value;
      }
    }
    return result;
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
