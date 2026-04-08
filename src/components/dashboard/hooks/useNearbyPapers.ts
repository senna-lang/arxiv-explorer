/**
 * 選択された論文のUMAP座標から近傍K件を計算するフック
 *
 * UMAP 2D空間でのユークリッド距離でソートし上位K件を返す。
 */

import { useMemo } from "react";
import type { DashboardPaper } from "../../../lib/types";

export function useNearbyPapers(
	selectedId: string | null,
	papers: DashboardPaper[],
	k: number = 10,
): DashboardPaper[] {
	return useMemo(() => {
		if (!selectedId) return [];
		const target = papers.find((p) => p.id === selectedId);
		if (!target) return [];

		const tx = target.umap_x;
		const ty = target.umap_y;

		return papers
			.filter((p) => p.id !== selectedId)
			.map((p) => ({
				paper: p,
				dist: (p.umap_x - tx) ** 2 + (p.umap_y - ty) ** 2,
			}))
			.sort((a, b) => a.dist - b.dist)
			.slice(0, k)
			.map((item) => item.paper);
	}, [selectedId, papers, k]);
}
