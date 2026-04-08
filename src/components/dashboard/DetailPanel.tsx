/**
 * 論文詳細パネル（右サイドバー）
 *
 * 選択された論文のタイトル・abstract・スコア・星評価・近傍論文を表示する。
 * フロストガラス + スライドインアニメーション。
 */

import type { Cluster, DashboardPaper, Rating } from "../../lib/types";
import { useNearbyPapers } from "./hooks/useNearbyPapers";
import { StarRating } from "./StarRating";

type Props = {
	paper: DashboardPaper;
	cluster: Cluster | undefined;
	allPapers: DashboardPaper[];
	rating: Rating | undefined;
	onRate: (paperId: string, title: string, abstract: string, rating: 1 | 2 | 3) => void;
	onSelectPaper: (id: string) => void;
	onClose: () => void;
};

export function DetailPanel({
	paper,
	cluster,
	allPapers,
	rating,
	onRate,
	onSelectPaper,
	onClose,
}: Props) {
	const nearby = useNearbyPapers(paper.id, allPapers);
	const scorePercent = paper.score != null ? Math.round(paper.score * 100) : null;

	return (
		<div className="detail-panel">
			<button onClick={onClose} className="detail-panel__close">
				✕
			</button>

			<h2 className="detail-panel__title">
				<a href={paper.url} target="_blank" rel="noopener noreferrer">
					{paper.title ?? paper.id}
				</a>
			</h2>

			<div className="detail-panel__meta">
				{paper.authors && (
					<span>
						{paper.authors.slice(0, 3).join(", ")}
						{paper.authors.length > 3 ? " et al." : ""}
					</span>
				)}
				{paper.categories && (
					<span className="detail-panel__category">{paper.categories[0]}</span>
				)}
				{scorePercent != null && (
					<span className="detail-panel__score">{scorePercent}%</span>
				)}
			</div>

			<div className="detail-panel__actions">
				<StarRating
					rating={rating?.rating ?? 0}
					onRate={(v) => onRate(paper.id, paper.title ?? paper.id, paper.abstract ?? "", v)}
				/>
				<a
					href={`https://arxiv.org/pdf/${paper.id}`}
					target="_blank"
					rel="noopener noreferrer"
					className="detail-panel__link detail-panel__link--pdf"
				>
					PDF
				</a>
				{paper.github_url && (
					<a
						href={paper.github_url}
						target="_blank"
						rel="noopener noreferrer"
						className="detail-panel__link detail-panel__link--gh"
					>
						GitHub
					</a>
				)}
			</div>

			{cluster && (
				<div className="detail-panel__cluster">
					<span className="detail-panel__cluster-label">
						{cluster.label}
					</span>
					<span className="detail-panel__cluster-size">{cluster.size}</span>
				</div>
			)}

			{paper.abstract && (
				<div>
					<h3 className="detail-panel__section-title">Abstract</h3>
					<p className="detail-panel__abstract">{paper.abstract}</p>
				</div>
			)}

			<div className="detail-panel__nearby">
				<h3 className="detail-panel__section-title">Nearby Papers</h3>
				<ul className="detail-panel__nearby-list">
					{nearby.map((np) => (
						<li key={np.id} className="detail-panel__nearby-item">
							<button
								onClick={() => onSelectPaper(np.id)}
								className="detail-panel__nearby-btn"
							>
								{np.title ?? np.id}
							</button>
						</li>
					))}
				</ul>
			</div>
		</div>
	);
}
