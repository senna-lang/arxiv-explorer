/**
 * useNearbyPapers ロジックのテスト
 *
 * UMAP 2D空間でのユークリッド距離に基づく近傍論文計算を検証する。
 * フックの純粋なロジック部分を直接テストする。
 */

import { describe, expect, it } from "bun:test";
import type { DashboardPaper } from "../src/lib/types";

/** フックの内部ロジックを直接テスト（React依存を排除） */
function computeNearby(
	selectedId: string,
	papers: DashboardPaper[],
	k: number,
): DashboardPaper[] {
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
}

function makePaper(id: string, x: number, y: number): DashboardPaper {
	return {
		id,
		umap_x: x,
		umap_y: y,
		cluster_id: 0,
		url: `https://arxiv.org/abs/${id}`,
	};
}

describe("computeNearby", () => {
	const papers: DashboardPaper[] = [
		makePaper("A", 0, 0),
		makePaper("B", 1, 0),
		makePaper("C", 3, 0),
		makePaper("D", 0, 4),
		makePaper("E", 10, 10),
	];

	it("距離順に近い論文を返す", () => {
		const result = computeNearby("A", papers, 3);
		expect(result.map((p) => p.id)).toEqual(["B", "C", "D"]);
	});

	it("自分自身は含めない", () => {
		const result = computeNearby("A", papers, 10);
		expect(result.find((p) => p.id === "A")).toBeUndefined();
		expect(result).toHaveLength(4);
	});

	it("k が全件数より大きい場合は全件返す", () => {
		const result = computeNearby("A", papers, 100);
		expect(result).toHaveLength(4);
	});

	it("存在しないIDの場合は空配列を返す", () => {
		const result = computeNearby("Z", papers, 3);
		expect(result).toEqual([]);
	});
});
