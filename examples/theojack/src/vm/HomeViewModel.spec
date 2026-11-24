#! Package theojack:vm
#! ViewModel for the TheoJack home screen: manages hero card rotation, active card style, About dialog state, and navigation intents.

Class is HomeViewModel{
	replace [String] is namespace: ['theojack', 'vm'];

	merge [[String]] is using: [
		['base', 'signal', [BoolEmitter, EnumEmitter]],
		['base', 'sys', as Time()],
		['theojack', 'model', [Card, CardStyle]]
	];

	Card is heroCard: Card();
	EnumEmitter of CardStyle is cardStyle: EnumEmitter(initial: CardStyle:WIREFRAME);
	BoolEmitter is aboutOpen: BoolEmitter(initial: false);
	Int is lastCardMs: 0;
	Function is onCardChanged: local Function(Card is _c){};
	Function is onOpenPlay: {};
	Function is onOpenRules: {};
	Function is onOpenOptions: {};
	Function is onQuit: {};

	replace Function is init(
		CardStyle is initialStyle: CardStyle:WIREFRAME,
		Function is onOpenPlay: {},
		Function is onOpenRules: {},
		Function is onOpenOptions: {},
		Function is onQuit: {}
	){
		:heroCard: Card():randomCard();
		:cardStyle: EnumEmitter(initial: initialStyle);
		:aboutOpen: BoolEmitter(initial: false);
		:lastCardMs: monotonicMs();
		:onOpenPlay: onOpenPlay;
		:onOpenRules: onOpenRules;
		:onOpenOptions: onOpenOptions;
		:onQuit: onQuit;
	}

	Function is setCardStyle(CardStyle is next){
		cardStyle:emit(value: next);
	}

	Function is randomizeCard(){
		:heroCard: Card():randomCard();
		:lastCardMs: monotonicMs();
		onCardChanged(heroCard);
	}

	Function of Boolean is onTick(){
		if({ aboutOpen:current() }, { return false; });
		local Int is now: monotonicMs();
		if({ now - lastCardMs >= 1000 }, {
			randomizeCard();
			return true;
		});
		return false;
	}

	Function is play(){
		onOpenPlay();
	}

	Function is openRules(){
		onOpenRules();
	}

	Function is openOptions(){
		onOpenOptions();
	}

	Function is openAbout(){
		aboutOpen:emit(value: true);
	}

	Function is closeAbout(){
		aboutOpen:emit(value: false);
	}

	Function is quit(){
		onQuit();
	}
}
