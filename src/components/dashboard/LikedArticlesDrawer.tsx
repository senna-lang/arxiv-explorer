/**
 * いいね済み論文一覧ドロワー
 *
 * 評価済みの全論文をリスト表示する。ソート・フィルタ対応。
 */

import { useMemo, useState } from "react";
import type { DashboardPaper, Rating } from "../../lib/types";
import { StarRating } from "./StarRating";

type SortKey = "rating" | "score" | "date";

type Props = {
	papers: DashboardPaper[];
	ratings: Map<string, Rating>;
	onSelectPaper: (id: string) => void;
	onRate: (paperId: string, title: string, abstract: string, rating: 1 | 2 | 3) => void;
	isOpen: boolean;
	onToggle: () => void;
};

export function LikedArticlesDrawer({
	papers,
	ratings,
	onSelectPaper,
	onRate,
	isOpen,
	onToggle,
}: Props) {
	const [sortKey, setSortKey] = useState<SortKey>("rating");
	const [filterText, setFilterText] = useState("");

	const likedPapers = useMemo(() => {
		const paperMap = new Map(papers.map((p) => [p.id, p]));
		const liked: Array<{ paper: DashboardPaper; rating: Rating }> = [];

		for (const [paperId, rating] of ratings) {
			const paper = paperMap.get(paperId);
			if (paper) {
				liked.push({ paper, rating });
			}
		}

		const filtered = filterText
			? liked.filter(
					({ paper }) =>
						(paper.title ?? "").toLowerCase().includes(filterText.toLowerCase()) ||
						paper.id.includes(filterText),
				)
			: liked;

		filtered.sort((a, b) => {
			if (sortKey === "rating") return b.rating.rating - a.rating.rating;
			if (sortKey === "score") return (b.paper.score ?? 0) - (a.paper.score ?? 0);
			return (b.rating.rated_at ?? "").localeCompare(a.rating.rated_at ?? "");
		});

		return filtered;
	}, [papers, ratings, sortKey, filterText]);

	return (
		<div className="liked-drawer">
			<button onClick={onToggle} className="liked-drawer__toggle">
				{isOpen ? "▾" : "▴"} Starred ({ratings.size})
			</button>

			{isOpen && (
				<div className="liked-drawer__content">
					<div className="liked-drawer__controls">
						<input
							type="text"
							placeholder="Filter starred..."
							value={filterText}
							onChange={(e) => setFilterText(e.target.value)}
							className="liked-drawer__search"
						/>
						<select
							value={sortKey}
							onChange={(e) => setSortKey(e.target.value as SortKey)}
							className="liked-drawer__sort"
						>
							<option value="rating">By rating</option>
							<option value="score">By score</option>
							<option value="date">By date</option>
						</select>
					</div>

					{likedPapers.length === 0 ? (
						<p className="liked-drawer__empty">
							{ratings.size === 0
								? "No starred papers yet"
								: "No matches"}
						</p>
					) : (
						<div>
							{likedPapers.map(({ paper, rating }) => (
								<div key={paper.id} className="liked-drawer__row">
									<button
										onClick={() => onSelectPaper(paper.id)}
										className="liked-drawer__title-btn"
									>
										{paper.title ?? paper.id}
									</button>
									<div className="liked-drawer__row-right">
										{paper.score != null && (
											<span className="liked-drawer__row-score">
												{Math.round(paper.score * 100)}%
											</span>
										)}
										<StarRating
											rating={rating.rating}
											onRate={(v) =>
												onRate(
													paper.id,
													paper.title ?? paper.id,
													paper.abstract ?? "",
													v,
												)
											}
											size="sm"
										/>
									</div>
								</div>
							))}
						</div>
					)}
				</div>
			)}
		</div>
	);
}
