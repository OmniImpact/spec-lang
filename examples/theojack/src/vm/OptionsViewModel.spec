#! Package theojack:vm
#! ViewModel for the TheoJack options screen: holds pending option values and coordinates save/cancel persistence.

Class is OptionsViewModel{
	replace [String] is namespace: ['theojack', 'vm'];

	merge [[String]] is using: [
		['base', 'signal', [EnumEmitter, IntEmitter]],
		['theojack', 'model', CardStyle],
		['theojack', 'util', OptionsStorage]
	];

	OptionsStorage is storage: OptionsStorage();
	EnumEmitter of CardStyle is selectedStyle: EnumEmitter(initial: CardStyle:WIREFRAME);
	IntEmitter is selectedAmount: IntEmitter(initial: 500);
	IntEmitter is selectedRounds: IntEmitter(initial: 10);
	Function is onCancel: {};
	Function is onSave: local Function(CardStyle is _s){};

	replace Function is init(
		OptionsStorage is storage: OptionsStorage(),
		CardStyle is initialStyle: CardStyle:WIREFRAME,
		Int is initialAmount: 500,
		Int is initialRounds: 10,
		Function is onCancel: {},
		Function is onSave: local Function(CardStyle is _s){}
	){
		:storage: storage;
		:selectedStyle: EnumEmitter(initial: initialStyle);
		:selectedAmount: IntEmitter(initial: initialAmount);
		:selectedRounds: IntEmitter(initial: initialRounds);
		:onCancel: onCancel;
		:onSave: onSave;
	}

	Function is selectStyle(CardStyle is next){
		selectedStyle:emit(value: next);
	}

	Function is selectStyleByName(String is name){
		selectStyle(next: storage:styleFromName(name: name));
	}

	Function is selectAmount(Int is next){
		if({ next > 0 }, {
			selectedAmount:emit(value: next);
		});
	}

	Function is selectAmountText(String is raw){
		local Int is parsed: raw:trim() as Int;
		if({ parsed > 0 }, {
			selectedAmount:emit(value: parsed);
		});
	}

	Function is selectRounds(Int is next){
		if({ next > 0 }, {
			selectedRounds:emit(value: next);
		});
	}

	Function is cancel(){
		onCancel();
	}

	Function is save(){
		local CardStyle is style: selectedStyle:current();
		storage:save(
			style: style,
			startingAmount: selectedAmount:current(),
			numRounds: selectedRounds:current()
		);
		onSave(style);
	}
}
