/**
 * BLACKDARK Developer SDK — TypeScript/JavaScript client (#853).
 * Typed wrappers, retries, pagination, errors, version compatibility.
 * @version 1.0.0
 */

export interface BlackdarkClientOptions {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelayMs?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  cursor?: string;
  hasMore: boolean;
}

export class BlackdarkApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'BlackdarkApiError';
  }
}

export class BlackdarkClient {
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly retryDelayMs: number;
  static readonly VERSION = '1.0.0';

  constructor(options: BlackdarkClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.apiKey = options.apiKey;
    this.timeout = options.timeout ?? 20000;
    this.maxRetries = options.maxRetries ?? 3;
    this.retryDelayMs = options.retryDelayMs ?? 1000;
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = {
      Accept: 'application/json',
      'User-Agent': `blackdark-sdk/${BlackdarkClient.VERSION}`,
    };
    if (this.apiKey) {
      h['X-API-Key'] = this.apiKey;
    }
    return h;
  }

  private async request<T>(
    method: string,
    path: string,
    params?: Record<string, string>,
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }

    let lastError: Error | undefined;
    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeout);
        const response = await fetch(url.toString(), {
          method,
          headers: this.headers(),
          signal: controller.signal,
        });
        clearTimeout(timer);

        if (response.status === 429 && attempt < this.maxRetries) {
          const retryAfter = parseInt(response.headers.get('Retry-After') || '1', 10);
          await new Promise((r) => setTimeout(r, retryAfter * 1000 || this.retryDelayMs));
          continue;
        }

        if (!response.ok) {
          throw new BlackdarkApiError(
            `API error: ${response.status}`,
            response.status,
          );
        }
        return (await response.json()) as T;
      } catch (err) {
        lastError = err as Error;
        if (attempt < this.maxRetries) {
          await new Promise((r) => setTimeout(r, this.retryDelayMs * (attempt + 1)));
        }
      }
    }
    throw lastError ?? new Error('Request failed');
  }

  /** GET /api/v1/market/overview */
  async getMarketOverview(): Promise<Record<string, unknown>> {
    return this.request('GET', '/api/v1/market/overview');
  }

  /** GET /api/v1/onchain/metrics/{asset} */
  async getOnchainMetrics(asset: string): Promise<Record<string, unknown>> {
    return this.request('GET', `/api/v1/onchain/metrics/${asset}`);
  }

  /** GET /api/v1/risk/protocol/{protocolId} */
  async getProtocolRisk(protocolId: string): Promise<Record<string, unknown>> {
    return this.request('GET', `/api/v1/risk/protocol/${protocolId}`);
  }

  /** GET /api/v1/usage — with cursor pagination */
  async getUsage(cursor?: string): Promise<PaginatedResponse<Record<string, unknown>>> {
    const params: Record<string, string> = {};
    if (cursor) params.cursor = cursor;
    const result = await this.request<Record<string, unknown>>('GET', '/api/v1/usage', params);
    return {
      data: (result.entries as Record<string, unknown>[]) ?? [],
      cursor: result.next_cursor as string | undefined,
      hasMore: Boolean(result.has_more),
    };
  }
}
