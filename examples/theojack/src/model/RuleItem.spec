#! Package theojack:model
#! Pure data model for one entry in rules.json (`header`, `text`, `bullet`, or `cards`).

Class is RuleItem{
	replace [String] is namespace: ['theojack', 'model'];

	merge [[String]] is using: [
		['theojack', 'model', Card]
	];

	String is kind: 'text';
	String is text: '';
	[String] is bullets: [];
	[Card] is cards: [];

	replace Function is init(
		String is kind: 'text',
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
