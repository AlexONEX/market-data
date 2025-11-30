import { createWriteStream } from "fs";
import { mkdir } from "fs/promises";
import { resolve } from "path";
import { getLogger } from "./logger";

export interface CSVWriteOptions {
  readonly path: string;
  readonly headers: readonly string[];
  readonly rows: readonly (readonly unknown[])[];
}

export class CSVWriter {
  private readonly logger = getLogger();

  async write(options: CSVWriteOptions): Promise<void> {
    const { path, headers, rows } = options;

    const dir = resolve(path, "..");
    await mkdir(dir, { recursive: true });

    const filePath = resolve(path);
    const stream = createWriteStream(filePath, { encoding: "utf-8" });

    return new Promise((resolve, reject) => {
      stream.on("error", reject);

      stream.write(this.escapeCSVLine(headers) + "\n");

      for (const row of rows) {
        stream.write(this.escapeCSVLine(row) + "\n");
      }

      stream.end(() => {
        this.logger.info({ filePath }, "CSV written successfully");
        resolve();
      });
    });
  }

  private escapeCSVLine(values: readonly unknown[]): string {
    return values
      .map((value) => {
        if (value === null || value === undefined) {
          return "";
        }

        const str = String(value);

        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
          return `"${str.replace(/"/g, '""')}"`;
        }

        return str;
      })
      .join(",");
  }
}
