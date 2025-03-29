import pino from 'pino';

const logger = pino({
  level: import.meta.env.PROD ? 'info' : 'debug',
  transport: import.meta.env.DEV ? {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
    },
  } : undefined,
  base: {
    env: import.meta.env.MODE,
  },
  formatters: {
    level: (label) => {
      return { level: label };
    },
  },
  redact: {
    paths: ['password', 'email', 'token'],
    censor: '[REDACTED]',
  },
});

export const log = {
  info: (msg: string, data?: object) => logger.info(data, msg),
  error: (msg: string, error?: Error | unknown, data?: object) => {
    if (error instanceof Error) {
      logger.error({ ...data, error: { message: error.message, stack: error.stack } }, msg);
    } else {
      logger.error({ ...data, error }, msg);
    }
  },
  warn: (msg: string, data?: object) => logger.warn(data, msg),
  debug: (msg: string, data?: object) => logger.debug(data, msg),
};