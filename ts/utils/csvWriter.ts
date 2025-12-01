import * as fs from "fs";
import * as path from "path";

export class CsvWriter {
  writeFile(filePath: string, data: unknown[][]): void {
    const csvContent = this.convertToCSV(data);
    const dir = path.dirname(filePath);

    if (dir && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(filePath, csvContent, "utf-8");
  }

  readFile(filePath: string): unknown[][] {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, "utf-8");
    return this.parseCSV(content);
  }

  private convertToCSV(data: unknown[][]): string {
    return data.map((row) => this.escapeRow(row)).join("\n");
  }

  private escapeRow(row: unknown[]): string {
    return row
      .map((cell) => {
        const str = String(cell ?? "");
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      })
      .join(",");
  }

  private parseCSV(content: string): unknown[][] {
    const lines = content.split("\n");
    const result: unknown[][] = [];

    for (const line of lines) {
      if (line.trim() === "") continue;
      result.push(this.parseRow(line));
    }

    return result;
  }

  private parseRow(line: string): unknown[] {
    const row: unknown[] = [];
    let current = "";
    let insideQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];

      if (char === '"') {
        if (insideQuotes && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          insideQuotes = !insideQuotes;
        }
      } else if (char === "," && !insideQuotes) {
        row.push(current);
        current = "";
      } else {
        current += char;
      }
    }

    row.push(current);
    return row;
  }
}
