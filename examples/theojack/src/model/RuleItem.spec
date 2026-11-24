#! Package theojack:model
#! Pure data model for one entry in rules.json (`header`, `text`, `bullet`, or `cards`).

Class is RuleItem{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['theojack', 'model', [Card, RuleKind]]
	];

	RuleKind is kind: RuleKind:TEXT;
	String is text: '';
	[String] is bullets: [];
	[Card] is cards: [];

	replace Function is init(
		RuleKind is kind: RuleKind:TEXT,
		String is text: '',
		[String] is bullets: [],
		[Card] is cards: []
	){
		:kind: kind;
		:text: text;
		:bullets: bullets;
		:cards: cards;
	}
}
