/**
 * 星評価保存APIエンドポイント
 *
 * POST /api/rate
 * Body: { paper_id: string, title: string, abstract: string, rating: number }
 *
 * 処理:
 * 1. Cloudflare KV から ratings を取得
 * 2. 同一paper_idがあれば上書き、なければ追記
 * 3. KV に保存して 200 OK を返す
 */
export const prerender = false;

import type { APIRoute } from "astro";
import type { Rating, RatingsData } from "../../lib/types";

export const GET: APIRoute = async ({ url }) => {
	const next = url.searchParams.get("next") || "/";
	return Response.redirect(next, 302);
};

export const POST: APIRoute = async ({ request, locals }) => {
	let body: {
		paper_id: string;
		title: string;
		abstract: string;
		rating: number;
	};
	try {
		body = await request.json();
	} catch {
		return new Response(JSON.stringify({ error: "Invalid JSON" }), {
			status: 400,
			headers: { "Content-Type": "application/json" },
		});
	}

	const { paper_id, title, abstract, rating } = body;
	if (
		!paper_id ||
		typeof rating !== "number" ||
		rating < 1 ||
		rating > 3 ||
		!Number.isInteger(rating)
	) {
		return new Response(JSON.stringify({ error: "Invalid parameters" }), {
			status: 400,
			headers: { "Content-Type": "application/json" },
		});
	}

	const kv = (locals.runtime?.env as Cloudflare.Env).RATINGS_KV;
	const existing = await kv.get("ratings");
	const data: RatingsData = existing ? JSON.parse(existing) : { ratings: [] };

	const rated_at = new Date().toISOString();
	const newEntry: Rating = {
		paper_id,
		title,
		abstract,
		rating: rating as 1 | 2 | 3,
		rated_at,
	};

	const idx = data.ratings.findIndex((r) => r.paper_id === paper_id);
	if (idx >= 0) {
		data.ratings[idx] = newEntry;
	} else {
		data.ratings.push(newEntry);
	}

	await kv.put("ratings", JSON.stringify(data));

	return new Response(JSON.stringify({ ok: true }), {
		status: 200,
		headers: { "Content-Type": "application/json" },
	});
};
