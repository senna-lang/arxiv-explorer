/**
 * フィルタバー
 *
 * キーワード検索・スコア範囲・クラスタ選択でフィルタリングする。
 */

import type { Cluster, FilterState } from "../../lib/types";

type Props = {
	filter: FilterState;
	clusters: Cluster[];
	onFilterChange: (filter: FilterState) => void;
};

export function FilterBar({ filter, clusters, onFilterChange }: Props) {
	const toggleCluster = (id: number) => {
		const next = new Set(filter.selectedClusterIds);
		if (next.has(id)) {
			next.delete(id);
		} else {
			next.add(id);
		}
		onFilterChange({ ...filter, selectedClusterIds: next });
	};

	const clearAll = () => {
		onFilterChange({
			keyword: "",
			scoreRange: [0, 100],
			selectedClusterIds: new Set(),
		});
	};

	const hasFilter =
		filter.keyword !== "" ||
		filter.scoreRange[0] > 0 ||
		filter.scoreRange[1] < 100 ||
		filter.selectedClusterIds.size > 0;

	return (
		<div className="filter-bar">
			<input
				type="text"
				placeholder="Search papers..."
				value={filter.keyword}
				onChange={(e) =>
					onFilterChange({ ...filter, keyword: e.target.value })
				}
				className="filter-bar__search"
			/>

			<div className="filter-bar__chips">
				{clusters.slice(0, 12).map((c) => (
					<button
						key={c.id}
						onClick={() => toggleCluster(c.id)}
						className={`filter-bar__chip ${
							filter.selectedClusterIds.has(c.id) ? "filter-bar__chip--active" : ""
						}`}
					>
						{c.label.split(" & ").slice(0, 2).join(" · ")}
					</button>
				))}
				{clusters.length > 12 && (
					<span className="filter-bar__more">+{clusters.length - 12}</span>
				)}
			</div>

			{hasFilter && (
				<button onClick={clearAll} className="filter-bar__clear">
					Clear
				</button>
			)}
		</div>
	);
}
