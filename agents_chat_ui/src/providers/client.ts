import { Client } from "@langchain/langgraph-sdk";
// NOTE

export function createClient(apiUrl: string, apiKey: string | undefined) {
  return new Client({
    apiKey,
    apiUrl,
  });
}
