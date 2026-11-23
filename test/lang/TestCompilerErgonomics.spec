#! specunit: suite

Class of SpecUnitTest is TestCompilerErgonomics{
	replace Array of Array of String is using: [
		['specunit', [SpecUnitTest, as Assert()]],
		['base', 'sys', [as Conditional(), as Loops()]],
		['base', 'signal', '*'],
		['base', 'theo', [TheoColor, TheoCell]]
	];

	Function is testDirectFunctionFieldCalls(){
		local String is seen: '';
		local ErgoCallbackHost is host: ErgoCallbackHost(
			onNotify: local Function(String is m){
				seen: m;
			},
			transform: local Function of Int(Int is x){
				x + 5;
			}
		);
		host:fire(msg: 'hello');
		Assert:areEqualString('hello', seen);
		Assert:areEqualInt(15, host:runTransform(v: 10));
		host:fireFromClosure(msg: 'nested');
		Assert:areEqualString('nested', seen);
		# Object-qualified Function field call:
		Assert:areEqualInt(25, host:transform(20));
	}

	Function is testArrayOfFunction(){
		local Int is sum: 0;
		local Array of Function is callbacks: Array();
		callbacks:add(item: { sum: sum + 1; });
		callbacks:add(item: { sum: sum + 10; });
		callbacks:add(item: { sum: sum + 100; });
		local Int is i: 0;
		while({ i < callbacks:length() }, {
			local Function is fn: callbacks:get(index: i);
			fn();
			i++;
		});
		Assert:areEqualInt(111, sum);
	}

	Function is testDefaultClosureParameters(){
		# Omit both closure params -> defaults must lower cleanly without corrupting ptr
		local ErgoCallbackHost is host: ErgoCallbackHost();
		host:fire(msg: 'noop');
		Assert:areEqualString('noop', host:lastMsg);
		Assert:areEqualInt(14, host:runTransform(v: 7));
	}

	Function is testSynthesizedSubclassFieldDefaults(){
		# 0-arg inherited init
		local ErgoHelperSub is sub0: ErgoHelperSub();
		Assert:areEqualInt(10, sub0:baseTag);
		Assert:areEqualInt(42, sub0:subDefault);
		Assert:areEqualString('ready', sub0:subLabel);

		# Parameterized inherited init
		local ErgoHelperSub is sub1: ErgoHelperSub(baseTag: 99);
		Assert:areEqualInt(99, sub1:baseTag);
		Assert:areEqualInt(42, sub1:subDefault);
		Assert:areEqualString('ready', sub1:subLabel);
	}

	Function is testGroupedAndWildcardImports(){
		# Wildcard ['base', 'signal', '*'] grants TextEmitter & IntEmitter
		local TextEmitter is te: TextEmitter(initial: 'ok');
		local IntEmitter is ie: IntEmitter(initial: 7);
		Assert:areEqualString('ok', te:current());
		Assert:areEqualInt(7, ie:current());
		# Grouped ['base', 'theo', [TheoColor, TheoCell]] grants both
		local TheoCell is cell: TheoCell();
		cell:ch: 'A';
		cell:fg: TheoColor:ansi(code: 7);
		Assert:areEqualString('A', cell:ch);
		Assert:areEqualInt(7, cell:fg:c1);
	}

	Function is testOverloadedWithDefaultedTrailingParams(){
		local ErgoOverloaded is a: ErgoOverloaded();
		Assert:areEqualString('string', a:kind);
		Assert:areEqualString('', a:text);
		Assert:areEqualInt(7, a:color);

		local ErgoOverloaded is b: ErgoOverloaded(value: 'hi');
		Assert:areEqualString('string', b:kind);
		Assert:areEqualString('hi', b:text);
		Assert:areEqualInt(7, b:color);
		Assert:isFalse(b:bold);

		local TextEmitter is em: TextEmitter(initial: 'live');
		local ErgoOverloaded is c: ErgoOverloaded(value: em, bold: true);
		Assert:areEqualString('emitter', c:kind);
		Assert:areEqualString('live', c:text);
		Assert:areEqualInt(7, c:color);
		Assert:isTrue(c:bold);

		Assert:areEqualString('pre:live!', c:format(prefix: 'pre'));
		Assert:areEqualString('42:live?', c:format(code: 42, suffix: '?'));
	}
}

Class is ErgoHelperBase{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	Int is baseTag: 10;

	replace Function is init(Int is baseTag: 10){
		:baseTag: baseTag;
	}
}

Class of ErgoHelperBase is ErgoHelperSub{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	Int is subDefault: 42;
	String is subLabel: 'ready';
}

Class is ErgoCallbackHost{
	replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
	];

	Function is onNotify: local Function(String is _msg){};
	Function of Int is transform: local Function of Int(Int is x){ x; };
	String is lastMsg: '';

	replace Function is init(
		Function is onNotify: local Function(String is _msg){},
		Function of Int is transform: local Function of Int(Int is x){ x * 2; }
	){
		:onNotify: onNotify;
		:transform: transform;
	}

	Function is fire(String is msg){
		:lastMsg: msg;
		onNotify(msg);
	}

	Function of Int is runTransform(Int is v){
		:transform(v);
	}

	Function is fireFromClosure(String is msg){
		local Function is thunk: {
			onNotify(msg);
		};
		thunk();
	}
}

Class is ErgoOverloaded{
	replace Array of Array of String is using: [
		['base', 'signal', TextEmitter],
		['base', 'sys', as Conditional()]
	];

	String is kind: '';
	String is text: '';
	Int is color: 7;
	Boolean is bold: false;

	replace Function is init(String is value: '', Int is color: 7, Boolean is bold: false){
		:kind: 'string';
		:text: value;
		:color: color;
		:bold: bold;
	}

	replace Function is init(TextEmitter is value, Int is color: 7, Boolean is bold: false){
		:kind: 'emitter';
		:text: value:current();
		:color: color;
		:bold: bold;
	}

	Function of String is format(String is prefix, String is suffix: '!'){
		"{{prefix}}:{{text}}{{suffix}}";
	}

	Function of String is format(Int is code, String is suffix: '!'){
		"{{code}}:{{text}}{{suffix}}";
	}
}
