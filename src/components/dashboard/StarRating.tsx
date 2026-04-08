/**
 * 星評価コンポーネント（React版）
 *
 * 1-3星をクリックで評価。ダークテーマでグロウエフェクト付き。
 */

type Props = {
	rating: number;
	onRate: (value: 1 | 2 | 3) => void;
	size?: "sm" | "md";
};

export function StarRating({ rating, onRate, size = "md" }: Props) {
	const fontSize = size === "sm" ? "1rem" : "1.4rem";

	return (
		<span className="star-rating">
			{([1, 2, 3] as const).map((n) => (
				<button
					key={n}
					onClick={(e) => {
						e.stopPropagation();
						onRate(n);
					}}
					aria-label={`${n} star`}
					className={`star-rating__btn ${n <= rating ? "star-rating__btn--active" : ""}`}
					style={{ fontSize, color: n <= rating ? undefined : "#ddd" }}
				>
					★
				</button>
			))}
		</span>
	);
}
