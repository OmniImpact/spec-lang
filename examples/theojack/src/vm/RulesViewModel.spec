#! Package theojack:vm
#! ViewModel for the TheoJack rules screen: loads structured [RuleItem]s and handles Done navigation.

Class is RulesViewModel{
	replace [String] is namespace: ['theojack', 'vm'];

	merge [[String]] is using: [
		['theojack', 'model', [CardStyle, RuleItem]],
		['theojack', 'util', RulesLoader]
	];

	RulesLoader is loader: RulesLoader();
	CardStyle is cardStyle: CardStyle:WIREFRAME;
	[RuleItem] is items: [];
	Function is onDone: {};

	replace Function is init(
		RulesLoader is loader: RulesLoader(),
		CardStyle is cardStyle: CardStyle:WIREFRAME,
		Function is onDone: {}
	){
		:loader: loader;
		:cardStyle: cardStyle;
		:items: loader:loadItems();
		:onDone: onDone;
	}

	Function is done(){
		onDone();
	}
}
