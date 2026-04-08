/**
 * ダッシュボード用データ構築ユーティリティ
 *
 * map.json の座標データと日次JSONの論文詳細をマージして
 * DashboardPaper 配列を構築する。ビルド時に Astro ページから呼ばれる。
 */

import type { DailyData, DashboardPaper, MapData, Paper } from "./types";

/**
 * 日次JSONの glob 結果から paperId → Paper の lookup を構築する
 */
function buildDailyLookup(
	dailyGlob: Record<string, unknown>,
): Map<string, Paper> {
	const lookup = new Map<string, Paper>();
	for (const mod of Object.values(dailyGlob)) {
		const daily = mod as { default?: DailyData } & DailyData;
		const data = daily.default ?? daily;
		if (!data.papers) continue;
		for (const paper of data.papers) {
			if (!lookup.has(paper.id)) {
				lookup.set(paper.id, paper);
			}
		}
	}
	return lookup;
}

/**
 * map.json + 日次JSON → DashboardPaper[] を構築
 */
export function buildDashboardPapers(
	mapData: MapData,
	dailyGlob: Record<string, unknown>,
): DashboardPaper[] {
	const dailyLookup = buildDailyLookup(dailyGlob);

	return mapData.papers.map((mp) => {
		const daily = dailyLookup.get(mp.id);
		const base: DashboardPaper = {
			...mp,
			title: mp.title ?? daily?.title ?? mp.id,
			abstract: mp.abstract ?? daily?.abstract,
			url: `https://arxiv.org/abs/${mp.id}`,
		};

		if (daily) {
			base.authors = daily.authors;
			base.categories = daily.categories;
			base.submitted = daily.submitted;
			base.score = daily.score;
			base.github_url = daily.github_url;
		}

		return base;
	});
}
