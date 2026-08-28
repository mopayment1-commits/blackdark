/**
 * Example: Market Overview — runnable in CI (#853).
 */
import { BlackdarkClient } from '../../typescript/blackdark-client';

async function main(): Promise<void> {
  const client = new BlackdarkClient({
    baseUrl: process.env.BLACKDARK_API_URL ?? 'https://api.blackdark.io',
    apiKey: process.env.BLACKDARK_API_KEY,
  });
  const overview = await client.getMarketOverview();
  console.log('Market overview:', overview);
}

main().catch(console.error);
