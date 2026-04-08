/**
 * deck.gl ベースの論文地図コンポーネント
 *
 * ScatterplotLayer で 10K 点を描画し、クラスタごとに色分けする。
 * TextLayer でラベルを描画（characterSet 指定でフォント問題を回避）。
 */

import { OrthographicView } from "@deck.gl/core";
import { ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import DeckGL from "@deck.gl/react";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { Cluster, DashboardPaper, Rating } from "../../lib/types";

export type MapViewHandle = {
	flyTo: (x: number, y: number) => void;
};

type Props = {
	papers: DashboardPaper[];
	clusters: Cluster[];
	ratings: Map<string, Rating>;
	selectedId: string | null;
	filteredIds: Set<string> | null;
	onSelectPaper: (id: string) => void;
	onReady?: (handle: MapViewHandle) => void;
};

const CLUSTER_COLORS: Array<[number, number, number]> = [
	[37, 99, 235], [5, 150, 105], [217, 119, 6], [220, 38, 38],
	[124, 58, 237], [219, 39, 119], [13, 148, 136], [234, 88, 12],
	[79, 70, 229], [147, 51, 234], [22, 163, 74], [8, 145, 178],
];

const NOISE_COLOR: [number, number, number] = [200, 200, 195];
const SELECTED_COLOR: [number, number, number] = [220, 38, 38];

function getClusterColor(clusterId: number | null): [number, number, number] {
	if (clusterId == null) return NOISE_COLOR;
	return CLUSTER_COLORS[clusterId % CLUSTER_COLORS.length];
}

type ViewState = { target: [number, number, number]; zoom: number };

type Bounds = { minX: number; maxX: number; minY: number; maxY: number };

function computeBounds(papers: DashboardPaper[]): Bounds {
	let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
	for (const p of papers) {
		if (p.umap_x < minX) minX = p.umap_x;
		if (p.umap_x > maxX) maxX = p.umap_x;
		if (p.umap_y < minY) minY = p.umap_y;
		if (p.umap_y > maxY) maxY = p.umap_y;
	}
	return { minX, maxX, minY, maxY };
}

function computeInitialView(papers: DashboardPaper[]): ViewState {
	if (papers.length === 0) return { target: [0, 0, 0], zoom: 3 };
	const b = computeBounds(papers);
	const cx = (b.minX + b.maxX) / 2;
	const cy = (b.minY + b.maxY) / 2;
	const range = Math.max(b.maxX - b.minX, b.maxY - b.minY, 1);
	return { target: [cx, cy, 0], zoom: Math.log2(800 / range) };
}


export function MapView({
	papers, clusters, ratings, selectedId, filteredIds, onSelectPaper, onReady,
}: Props) {
	const bounds = useMemo(() => computeBounds(papers), [papers]);
	const initialView = useMemo(() => computeInitialView(papers), [papers]);
	const [viewState, setViewState] = useState<ViewState>(initialView);

	// flyTo を親に公開
	const flyTo = useCallback((x: number, y: number) => {
		setViewState((prev) => ({
			...prev,
			target: [x, y, 0] as [number, number, number],
			zoom: Math.max(prev.zoom, initialView.zoom + 3),
		}));
	}, [initialView.zoom]);

	useEffect(() => {
		if (onReady) onReady({ flyTo });
	}, [onReady, flyTo]);

	const topClusters = useMemo(() => {
		return [...clusters].sort((a, b) => b.size - a.size).slice(0, 15);
	}, [clusters]);

	const paperLayer = useMemo(
		() =>
			new ScatterplotLayer<DashboardPaper>({
				id: "papers",
				data: papers,
				getPosition: (d) => [d.umap_x, d.umap_y, 0],
				getRadius: (d) => {
					if (d.id === selectedId) return 10;
					if (filteredIds && filteredIds.has(d.id)) return 7;
					if (ratings.has(d.id)) return 5;
					if (filteredIds && !filteredIds.has(d.id)) return 2;
					return 3;
				},
				getFillColor: (d) => {
					if (d.id === selectedId) return [...SELECTED_COLOR, 255];
					const base = getClusterColor(d.cluster_id);
					if (filteredIds && !filteredIds.has(d.id)) return [...base, 15];
					if (filteredIds && filteredIds.has(d.id)) return [...base, 240];
					if (ratings.has(d.id)) return [184, 134, 11, 220];
					return [...base, 160];
				},
				getLineColor: (d) => {
					if (d.id === selectedId) return [...SELECTED_COLOR, 255];
					if (filteredIds && filteredIds.has(d.id)) return [30, 30, 30, 180];
					if (ratings.has(d.id)) return [184, 134, 11, 180];
					return [0, 0, 0, 0];
				},
				getLineWidth: (d) => {
					if (d.id === selectedId) return 2;
					if (filteredIds && filteredIds.has(d.id)) return 1;
					return ratings.has(d.id) ? 1.5 : 0;
				},
				stroked: true,
				radiusUnits: "pixels",
				lineWidthUnits: "pixels",
				pickable: true,
				radiusMinPixels: 3,
				autoHighlight: true,
				highlightColor: [255, 255, 255, 60],
				onClick: (info) => {
					if (info.object) onSelectPaper(info.object.id);
				},
				updateTriggers: {
					getFillColor: [selectedId, filteredIds, ratings.size],
					getRadius: [selectedId, ratings.size],
					getLineColor: [selectedId, ratings.size],
					getLineWidth: [selectedId, ratings.size],
				},
			}),
		[papers, selectedId, filteredIds, ratings, onSelectPaper],
	);

	const labelLayer = useMemo(
		() =>
			new TextLayer<Cluster>({
				id: "cluster-labels",
				data: topClusters,
				getPosition: (d) => [d.umap_x, d.umap_y, 0],
				getText: (d) => d.label.split(" & ").slice(0, 2).join(" / "),
				getSize: 13,
				getColor: (d) => [...getClusterColor(d.id), 220],
				getTextAnchor: "middle",
				getAlignmentBaseline: "center",
				billboard: true,
				sizeUnits: "pixels",
				sizeMaxPixels: 15,
				sizeMinPixels: 8,
				background: true,
				getBackgroundColor: [255, 255, 255, 235],
				backgroundPadding: [6, 2],
			}),
		[topClusters],
	);

	const handleViewStateChange = useCallback(
		({ viewState: vs }: { viewState: Record<string, unknown> }) => {
			const next = vs as ViewState;
			// ズーム下限
			if (next.zoom < initialView.zoom) {
				next.zoom = initialView.zoom;
			}
			// パン範囲を点群の範囲内に制限
			const [tx, ty] = next.target;
			next.target = [
				Math.max(bounds.minX, Math.min(bounds.maxX, tx)),
				Math.max(bounds.minY, Math.min(bounds.maxY, ty)),
				0,
			];
			setViewState(next);
		},
		[initialView.zoom, bounds],
	);

	return (
		<div className="map-view">
			<DeckGL
				views={new OrthographicView({ id: "ortho" })}
				viewState={viewState}
				onViewStateChange={handleViewStateChange}
				layers={[paperLayer, labelLayer]}
				controller={true}
				style={{ position: "absolute", inset: "0" }}
				getCursor={({ isHovering }: { isHovering: boolean }) =>
					isHovering ? "pointer" : "grab"
				}
			/>
		</div>
	);
}
