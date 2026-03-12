/**
 * 星評価保存APIエンドポイント
 *
 * POST /api/rate
 * Body: { paper_id: string, title: string, abstract: string, rating: number }
 *
 * 処理:
 * 1. GitHub REST API で data/ratings.json を取得（SHA も取得）
 * 2. 同一paper_idがあれば上書き、なければ追記
 * 3. GitHub REST API で data/ratings.json を更新コミット
 * 4. 200 OK を返す
 *
 * 環境変数:
 *   GITHUB_TOKEN  - Personal Access Token（contents write権限）
 *   GITHUB_OWNER  - リポジトリオーナー名
 *   GITHUB_REPO   - リポジトリ名
 */
export const prerender = false;

import type { APIRoute } from "astro";
import type { Rating, RatingsData } from "../../lib/types";

const GITHUB_API = "https://api.github.com";
const FILE_PATH = "data/ratings.json";

async function getFileFromGitHub(
  owner: string,
  repo: string,
  token: string
): Promise<{ data: RatingsData; sha: string }> {
  const res = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/contents/${FILE_PATH}`,
    { headers: { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json" } }
  );
  if (!res.ok) {
    return { data: { ratings: [] }, sha: "" };
  }
  const json = await res.json() as { content: string; sha: string };
  const decoded = atob(json.content.replace(/\n/g, ""));
  return { data: JSON.parse(decoded) as RatingsData, sha: json.sha };
}

async function putFileToGitHub(
  owner: string,
  repo: string,
  token: string,
  data: RatingsData,
  sha: string,
  message: string
): Promise<void> {
  const encoded = new TextEncoder().encode(JSON.stringify(data, null, 2) + "\n");
  const content = btoa(String.fromCharCode(...encoded));
  const body: Record<string, string> = { message, content };
  if (sha) body.sha = sha;

  const res = await fetch(
    `${GITHUB_API}/repos/${owner}/${repo}/contents/${FILE_PATH}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    }
  );
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`GitHub PUT failed: ${err}`);
  }
}

export const POST: APIRoute = async ({ request }) => {
  const owner = import.meta.env.GITHUB_OWNER;
  const repo = import.meta.env.GITHUB_REPO;
  const token = import.meta.env.GITHUB_TOKEN;

  if (!owner || !repo || !token) {
    return new Response(JSON.stringify({ error: "GitHub env vars not set" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  let body: { paper_id: string; title: string; abstract: string; rating: number };
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: "Invalid JSON" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { paper_id, title, abstract, rating } = body;
  if (!paper_id || typeof rating !== "number" || rating < 1 || rating > 3) {
    return new Response(JSON.stringify({ error: "Invalid parameters" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const { data, sha } = await getFileFromGitHub(owner, repo, token);

  const rated_at = new Date().toISOString();
  const newEntry: Rating = { paper_id, title, abstract, rating, rated_at };

  const idx = data.ratings.findIndex((r) => r.paper_id === paper_id);
  if (idx >= 0) {
    data.ratings[idx] = newEntry;
  } else {
    data.ratings.push(newEntry);
  }

  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  try {
    await putFileToGitHub(owner, repo, token, data, sha, `rate: ${dateStr}`);
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};
