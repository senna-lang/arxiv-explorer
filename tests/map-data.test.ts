/**
 * buildDashboardPapers のテスト
 *
 * map.json の座標データと日次JSONの論文詳細をマージして
 * DashboardPaper 配列を正しく構築できることを検証する。
 */

import { describe, expect, it } from "bun:test";
import { buildDashboardPapers } from "../src/lib/map-data";
import type { DailyData, MapData } from "../src/lib/types";

function makeMapData(papers: MapData["papers"]): MapData {
	return {
		generated_at: "2026-04-01T00:00:00+09:00",
		total_papers: papers.length,
		model: "test",
		clusters: [
			{
				id: 0,
				keywords: ["test"],
				label: "test cluster",
				centroid: [0],
				paper_ids: papers.filter((p) => p.cluster_id === 0).map((p) => p.id),
				size: 1,
				umap_x: 0,
				umap_y: 0,
			},
		],
		papers,
	};
}

function makeDailyGlob(dailies: DailyData[]): Record<string, unknown> {
	const result: Record<string, unknown> = {};
	for (const d of dailies) {
		result[`/data/${d.date.replace(/-/g, "")}.json`] = { default: d };
	}
	return result;
}

describe("buildDashboardPapers", () => {
	it("map.json の論文に基本フィールドを付与する", () => {
		const mapData = makeMapData([
			{ id: "2603.00001", title: "Test Paper", umap_x: 1.0, umap_y: 2.0, cluster_id: 0 },
		]);
		const result = buildDashboardPapers(mapData, {});

		expect(result).toHaveLength(1);
		expect(result[0].id).toBe("2603.00001");
		expect(result[0].title).toBe("Test Paper");
		expect(result[0].url).toBe("https://arxiv.org/abs/2603.00001");
		expect(result[0].umap_x).toBe(1.0);
		expect(result[0].umap_y).toBe(2.0);
		expect(result[0].cluster_id).toBe(0);
	});

	it("日次JSONの詳細情報をマージする", () => {
		const mapData = makeMapData([
			{ id: "2603.00001", umap_x: 1.0, umap_y: 2.0, cluster_id: 0 },
		]);

		const daily: DailyData = {
			date: "2026-03-01",
			collected_at: "2026-03-01T00:00:00+09:00",
			papers: [
				{
					id: "2603.00001",
					title: "Daily Title",
					authors: ["Author A"],
					abstract: "Some abstract text",
					url: "https://arxiv.org/abs/2603.00001",
					categories: ["cs.AI"],
					submitted: "2026-02-28",
					score: 0.85,
				},
			],
			meta: { total: 100, model: "test", profile_version: "v1" },
		};

		const result = buildDashboardPapers(mapData, makeDailyGlob([daily]));

		expect(result[0].abstract).toBe("Some abstract text");
		expect(result[0].authors).toEqual(["Author A"]);
		expect(result[0].categories).toEqual(["cs.AI"]);
		expect(result[0].score).toBe(0.85);
		expect(result[0].submitted).toBe("2026-02-28");
	});

	it("日次JSONに存在しない論文はタイトルにIDをフォールバックする", () => {
		const mapData = makeMapData([
			{ id: "2603.99999", umap_x: 0, umap_y: 0, cluster_id: null },
		]);

		const result = buildDashboardPapers(mapData, {});

		expect(result[0].title).toBe("2603.99999");
		expect(result[0].abstract).toBeUndefined();
		expect(result[0].score).toBeUndefined();
	});

	it("map.json にタイトルがあれば日次JSONより優先する", () => {
		const mapData = makeMapData([
			{ id: "2603.00001", title: "Map Title", umap_x: 0, umap_y: 0, cluster_id: 0 },
		]);

		const daily: DailyData = {
			date: "2026-03-01",
			collected_at: "2026-03-01T00:00:00+09:00",
			papers: [
				{
					id: "2603.00001",
					title: "Daily Title",
					authors: [],
					abstract: "abs",
					url: "",
					categories: [],
					submitted: "2026-02-28",
					score: 0.5,
				},
			],
			meta: { total: 1, model: "test", profile_version: "v1" },
		};

		const result = buildDashboardPapers(mapData, makeDailyGlob([daily]));
		expect(result[0].title).toBe("Map Title");
	});
});
