import { mkdir, writeFile } from "fs/promises";
import { resolve } from "path";
import { getLogger } from "./logger";

export interface JSONWriteOptions {
  readonly path: string;
  readonly data: unknown;
}

export class JSONWriter {
  private readonly logger = getLogger();

  async write(options: JSONWriteOptions): Promise<void> {
    const { path, data } = options;

    const dir = resolve(path, "..");
    await mkdir(dir, { recursive: true });

    const filePath = resolve(path);
    const content = JSON.stringify(data, null, 2);

    await writeFile(filePath, content, { encoding: "utf-8" });

    this.logger.info({ filePath }, "JSON written successfully");
  }
}
