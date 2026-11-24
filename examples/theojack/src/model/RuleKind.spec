#! Package theojack:model
#! Kind of one entry in rules.json.

Enum of String is RuleKind{
	replace [String] is namespace: ['theojack', 'model'];

	HEADER: 'header',
	TEXT: 'text',
	BULLET: 'bullet',
	CARDS: 'cards'
}
