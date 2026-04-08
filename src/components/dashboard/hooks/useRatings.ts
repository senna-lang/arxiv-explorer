/**
 * 評価データの取得・送信を管理するフック
 *
 * マウント時に GET /api/ratings で評価一覧を取得する。
 * APIが空または失敗時は initialRatings（ビルド時の ratings.json）をフォールバックとして使う。
 * rate() で POST /api/rate を呼んで楽観的にローカル状態を更新する。
 */

import { useCallback, useEffect, useState } from "react";
import type { Rating } from "../../../lib/types";

type RatingsMap = Map<string, Rating>;

type UseRatingsReturn = {
	ratings: RatingsMap;
	rate: (paperId: string, title: string, abstract: string, rating: 1 | 2 | 3) => Promise<void>;
	loading: boolean;
};

function toMap(ratings: Rating[]): RatingsMap {
	const map = new Map<string, Rating>();
	for (const r of ratings) {
		map.set(r.paper_id, r);
	}
	return map;
}

export function useRatings(initialRatings: Rating[] = []): UseRatingsReturn {
	const [ratings, setRatings] = useState<RatingsMap>(() => toMap(initialRatings));
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		let cancelled = false;
		(async () => {
			try {
				const res = await fetch("/api/ratings");
				if (!res.ok) return;
				const data = (await res.json()) as { ratings: Rating[] };
				if (cancelled) return;
				// APIに評価データがあればそちらを使う。なければ初期値を維持
				if (data.ratings.length > 0) {
					setRatings(toMap(data.ratings));
				}
			} catch {
				// KV未接続時は initialRatings をそのまま使う
			} finally {
				if (!cancelled) setLoading(false);
			}
		})();
		return () => { cancelled = true; };
	}, []);

	const rate = useCallback(
		async (paperId: string, title: string, abstract: string, rating: 1 | 2 | 3) => {
			setRatings((prev) => {
				const next = new Map(prev);
				next.set(paperId, {
					paper_id: paperId,
					title,
					abstract,
					rating,
					rated_at: new Date().toISOString(),
				});
				return next;
			});

			try {
				const res = await fetch("/api/rate", {
					method: "POST",
					credentials: "include",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify({ paper_id: paperId, title, abstract, rating }),
				});

				if (res.status === 401 || res.status === 403) {
					window.location.href = `/api/rate?next=${encodeURIComponent(window.location.href)}`;
					return;
				}

				if (!res.ok) {
					setRatings((prev) => {
						const next = new Map(prev);
						next.delete(paperId);
						return next;
					});
				}
			} catch {
				window.location.href = `/api/rate?next=${encodeURIComponent(window.location.href)}`;
			}
		},
		[],
	);

	return { ratings, rate, loading };
}
