/**
 * フィルタ結果リスト（左サイドバー）
 *
 * キーワード検索やクラスタ選択でヒットした論文をリスト表示する。
 * 論文クリックでその位置にズーム + DetailPanel 表示。
 */

import { useMemo } from "react";
import type { DashboardPaper, Rating } from "../../lib/types";
import { StarRating } from "./StarRating";

type Props = {
	papers: DashboardPaper[];
	filteredIds: Set<string>;
	ratings: Map<string, Rating>;
	selectedId: string | null;
	onSelectPaper: (id: string) => void;
	onRate: (paperId: string, title: string, abstract: string, rating: 1 | 2 | 3) => void;
};

export function FilterResults({
	papers,
	filteredIds,
	ratings,
	selectedId,
	onSelectPaper,
	onRate,
}: Props) {
	const filtered = useMemo(() => {
		return papers.filter((p) => filteredIds.has(p.id));
	}, [papers, filteredIds]);

	return (
		<div className="filter-results">
			<div className="filter-results__header">
				<span className="filter-results__count">{filtered.length} results</span>
			</div>
			<div className="filter-results__list">
				{filtered.map((p) => {
					const r = ratings.get(p.id);
					const isSelected = p.id === selectedId;
					return (
						<button
							key={p.id}
							className={`filter-results__item ${isSelected ? "filter-results__item--selected" : ""}`}
							onClick={() => onSelectPaper(p.id)}
						>
							<div className="filter-results__title">
								{p.title ?? p.id}
							</div>
							<div className="filter-results__meta">
								{p.categories?.[0] && (
									<span className="filter-results__category">{p.categories[0]}</span>
								)}
								<StarRating
									rating={r?.rating ?? 0}
									onRate={(v) => onRate(p.id, p.title ?? p.id, p.abstract ?? "", v)}
									size="sm"
								/>
							</div>
						</button>
					);
				})}
			</div>
		</div>
	);
}
