/**
 * Example: Cursor pagination — runnable in CI (#853).
 */
import { BlackdarkClient } from '../../typescript/blackdark-client';

async function main(): Promise<void> {
  const client = new BlackdarkClient({
    baseUrl: process.env.BLACKDARK_API_URL ?? 'https://api.blackdark.io',
    apiKey: process.env.BLACKDARK_API_KEY,
  });

  let cursor: string | undefined;
  let page = 0;
  do {
    const result = await client.getUsage(cursor);
    page += 1;
    console.log(`Page ${page}: ${result.data.length} entries`);
    cursor = result.hasMore ? result.cursor : undefined;
  } while (cursor);
}

main().catch(console.error);
