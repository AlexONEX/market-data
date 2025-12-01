import { google } from "googleapis";

export interface GoogleSheetsConfig {
  credentialsPath: string;
}

export class GoogleSheetsClient {
  private auth: InstanceType<typeof google.auth.GoogleAuth> | null = null;
  private sheets = google.sheets("v4");

  async initialize(credentialsPath: string): Promise<void> {
    this.auth = new google.auth.GoogleAuth({
      keyFile: credentialsPath,
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });
  }

  async getOrCreateSpreadsheet(
    spreadsheetName: string,
    spreadsheetId?: string
  ): Promise<string> {
    if (!this.auth) {
      throw new Error("GoogleSheetsClient not initialized");
    }

    if (spreadsheetId) {
      return spreadsheetId;
    }

    const authClient = await this.auth.getClient();
    const response = await this.sheets.spreadsheets.create(
      {
        auth: authClient as never,
        requestBody: {
          properties: {
            title: spreadsheetName,
          },
        },
      },
      {}
    );

    if (!response.data.spreadsheetId) {
      throw new Error("Failed to create spreadsheet");
    }

    return response.data.spreadsheetId;
  }

  async writeData(
    spreadsheetId: string,
    sheetName: string,
    data: unknown[][]
  ): Promise<void> {
    if (!this.auth) {
      throw new Error("GoogleSheetsClient not initialized");
    }

    const authClient = await this.auth.getClient();

    await this.sheets.spreadsheets.values.update(
      {
        auth: authClient as never,
        spreadsheetId,
        range: `${sheetName}!A1`,
        valueInputOption: "RAW",
        requestBody: {
          values: data,
        },
      },
      {}
    );
  }

  async appendData(
    spreadsheetId: string,
    sheetName: string,
    data: unknown[][]
  ): Promise<void> {
    if (!this.auth) {
      throw new Error("GoogleSheetsClient not initialized");
    }

    const authClient = await this.auth.getClient();

    await this.sheets.spreadsheets.values.append(
      {
        auth: authClient as never,
        spreadsheetId,
        range: `${sheetName}!A1`,
        valueInputOption: "RAW",
        requestBody: {
          values: data,
        },
      },
      {}
    );
  }

  async clearSheet(spreadsheetId: string, sheetName: string): Promise<void> {
    if (!this.auth) {
      throw new Error("GoogleSheetsClient not initialized");
    }

    const authClient = await this.auth.getClient();

    await this.sheets.spreadsheets.values.clear(
      {
        auth: authClient as never,
        spreadsheetId,
        range: `${sheetName}!A:Z`,
      },
      {}
    );
  }
}
