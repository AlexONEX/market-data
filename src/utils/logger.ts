import pino from "pino";

import { AppConfig } from "../domain";

let loggerInstance: pino.Logger;

export function initializeLogger(config: AppConfig): void {
  loggerInstance = pino(
    {
      level: config.logLevel,
      transport:
        config.nodeEnv === "development"
          ? {
              target: "pino-pretty",
              options: {
                colorize: true,
                singleLine: false,
                translateTime: "SYS:standard",
                ignore: "pid,hostname",
              },
            }
          : undefined,
    },
    pino.destination(1),
  );
}

export function getLogger(): pino.Logger {
  if (!loggerInstance) {
    loggerInstance = pino({
      level: "info",
      transport: {
        target: "pino-pretty",
        options: {
          colorize: true,
          singleLine: false,
        },
      },
    });
  }
  return loggerInstance;
}

export function createChildLogger(context: Record<string, unknown>): pino.Logger {
  return getLogger().child(context);
}

export default getLogger();
