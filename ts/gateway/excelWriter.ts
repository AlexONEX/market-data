import * as XLSX from "xlsx";
import * as fs from "fs";

export interface ExcelSheet {
  name: string;
  data: unknown[][];
}

export class ExcelWriter {
  writeFile(filePath: string, sheets: ExcelSheet[]): void {
    const workbook = XLSX.utils.book_new();

    for (const sheet of sheets) {
      const worksheet = XLSX.utils.aoa_to_sheet(sheet.data);
      XLSX.utils.book_append_sheet(workbook, worksheet, sheet.name);
    }

    const dir = filePath.split("/").slice(0, -1).join("/");
    if (dir && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    XLSX.writeFile(workbook, filePath);
  }

  readFile(filePath: string, sheetName?: string): unknown[][] {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const workbook = XLSX.readFile(filePath);
    const sheet = sheetName || workbook.SheetNames[0];

    if (!sheet) {
      throw new Error("No sheets found in workbook");
    }

    const worksheet = workbook.Sheets[sheet];
    if (!worksheet) {
      throw new Error(`Sheet "${sheet}" not found`);
    }

    const data = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
    return data as unknown[][];
  }
}
