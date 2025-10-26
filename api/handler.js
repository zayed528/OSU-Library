import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, ScanCommand } from "@aws-sdk/lib-dynamodb";

const client = new DynamoDBClient({ region: process.env.AWS_REGION || "us-east-1" });
const ddb = DynamoDBDocumentClient.from(client);
const TABLE = process.env.TABLE_NAME;

export const getSummary = async () => {
  try {
    const out = await ddb.send(new ScanCommand({ TableName: TABLE }));
    const totalSeats = out.Count || 0;
    const occupied = out.Items?.filter(x => x.status === "occupied").length || 0;
    const available = totalSeats - occupied;
    const rate = ((occupied / totalSeats) * 100).toFixed(1);
    return ok({ totalSeats, available, occupied, occupancyRate: rate });
  } catch (err) {
    console.error(err);
    return fail(err.message);
  }
};

const ok = (data) => ({
  statusCode: 200,
  headers: {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://zayed528.github.io",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
  },
  body: JSON.stringify(data)
});

const fail = (msg) => ({
  statusCode: 500,
  headers: { "Access-Control-Allow-Origin": "*" },
  body: JSON.stringify({ error: msg })
});
