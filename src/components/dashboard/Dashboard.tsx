/**
 * ダッシュボード本体
 *
 * 地図・フィルタ・詳細パネル・いいね一覧を統合管理する。
 * Dark Observatory テーマ。
 */

import { useCallback, useMemo, useRef, useState } from "react";
import type { Cluster, DashboardPaper, FilterState, Rating } from "../../lib/types";
import "./dashboard.css";
import { DetailPanel } from "./DetailPanel";
import { FilterBar } from "./FilterBar";
import { useRatings } from "./hooks/useRatings";
import { LikedArticlesDrawer } from "./LikedArticlesDrawer";
import { FilterResults } from "./FilterResults";
import { MapView } from "./MapView";
import type { MapViewHandle } from "./MapView";

type Props = {
	papers: DashboardPaper[];
	clusters: Cluster[];
	initialRatings: Rating[];
};

const INITIAL_FILTER: FilterState = {
	keyword: "",
	scoreRange: [0, 100],
	selectedClusterIds: new Set(),
};

export function Dashboard({ papers, clusters, initialRatings }: Props) {
	const [selectedId, setSelectedId] = useState<string | null>(null);
	const [filter, setFilter] = useState<FilterState>(INITIAL_FILTER);
	const [drawerOpen, setDrawerOpen] = useState(false);
	const { ratings, rate, loading } = useRatings(initialRatings);
	const mapRef = useRef<MapViewHandle | null>(null);

	const clusterMap = useMemo(
		() => new Map(clusters.map((c) => [c.id, c])),
		[clusters],
	);

	const paperMap = useMemo(
		() => new Map(papers.map((p) => [p.id, p])),
		[papers],
	);

	const filteredIds = useMemo(() => {
		const hasFilter =
			filter.keyword !== "" ||
			filter.scoreRange[0] > 0 ||
			filter.scoreRange[1] < 100 ||
			filter.selectedClusterIds.size > 0;

		if (!hasFilter) return null;

		const keyword = filter.keyword.toLowerCase();
		const ids = new Set<string>();

		for (const p of papers) {
			if (
				filter.selectedClusterIds.size > 0 &&
				(p.cluster_id == null || !filter.selectedClusterIds.has(p.cluster_id))
			) {
				continue;
			}

			if (p.score != null) {
				const pct = Math.round(p.score * 100);
				if (pct < filter.scoreRange[0] || pct > filter.scoreRange[1]) {
					continue;
				}
			}

			if (keyword) {
				const title = (p.title ?? "").toLowerCase();
				const clusterLabel =
					p.cluster_id != null
						? (clusterMap.get(p.cluster_id)?.label ?? "").toLowerCase()
						: "";
				if (!title.includes(keyword) && !clusterLabel.includes(keyword)) {
					continue;
				}
			}

			ids.add(p.id);
		}

		return ids;
	}, [papers, filter, clusterMap]);

	const selectedPaper = selectedId ? paperMap.get(selectedId) : undefined;
	const selectedCluster =
		selectedPaper?.cluster_id != null
			? clusterMap.get(selectedPaper.cluster_id)
			: undefined;

	const handleSelectPaper = useCallback((id: string) => {
		setSelectedId(id);
	}, []);

	/** 近傍論文リスト/いいね一覧から選択 → その論文にズーム */
	const handleNavigateToPaper = useCallback((id: string) => {
		setSelectedId(id);
		const paper = paperMap.get(id);
		if (paper && mapRef.current) {
			mapRef.current.flyTo(paper.umap_x, paper.umap_y);
		}
	}, [paperMap]);

	const handleClearFilter = useCallback(() => {
		setFilter(INITIAL_FILTER);
	}, []);

	const handleRate = useCallback(
		(paperId: string, title: string, abstract: string, ratingValue: 1 | 2 | 3) => {
			rate(paperId, title, abstract, ratingValue);
		},
		[rate],
	);

	return (
		<div className="dashboard-root">
			<FilterBar
				filter={filter}
				clusters={clusters}
				onFilterChange={setFilter}
			/>

			<div className="dashboard-main">
				{filteredIds && (
					<FilterResults
						papers={papers}
						filteredIds={filteredIds}
						ratings={ratings}
						selectedId={selectedId}
						onSelectPaper={handleNavigateToPaper}
						onRate={handleRate}
						onClose={handleClearFilter}
					/>
				)}

				<MapView
					papers={papers}
					clusters={clusters}
					ratings={ratings}
					selectedId={selectedId}
					filteredIds={filteredIds}
					onSelectPaper={handleSelectPaper}
					onReady={(h) => { mapRef.current = h; }}
				/>

				{selectedPaper && (
					<DetailPanel
						paper={selectedPaper}
						cluster={selectedCluster}
						allPapers={papers}
						rating={ratings.get(selectedPaper.id)}
						onRate={handleRate}
						onSelectPaper={handleNavigateToPaper}
						onClose={() => setSelectedId(null)}
					/>
				)}
			</div>

			<LikedArticlesDrawer
				papers={papers}
				ratings={ratings}
				onSelectPaper={handleNavigateToPaper}
				onRate={handleRate}
				isOpen={drawerOpen}
				onToggle={() => setDrawerOpen(!drawerOpen)}
			/>

			{loading && (
				<div className="dashboard-loading">
					Loading ratings...
				</div>
			)}
		</div>
	);
}
