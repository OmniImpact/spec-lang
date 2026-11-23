#! TypeChecker port check: bidirectional container typing, the
#! Array-of-X element fix, FIELD_ACCESS on call results, error paths,
#! and clean programs.

Class of SpecUnitTest is TestSpecChecker{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', Error],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Parses and checks a source, returning the error messages.
	##
	## @param src: Spec source text.
	## @return: Rendered type errors (empty when clean).
	Function of Array of String is checkOf(String is src){
		local [ClassInfo] is all: [];
		local Array of String is preloads: Array(['spec/lib/base/core/Mergeable.spec', 'spec/lib/base/sys/Conditional.spec', 'spec/lib/base/iterator/Loop.spec', 'spec/lib/base/iterator/LoopControl.spec', 'spec/lib/base/sys/Loops.spec', 'spec/lib/base/sys/Mem.spec', 'spec/lib/base/sys/SpinLock.spec', 'spec/lib/base/sys/Buf.spec', 'spec/lib/base/core/Str.spec', 'spec/lib/base/core/String.spec', 'spec/lib/base/struct/List.spec', 'spec/lib/base/struct/Array.spec', 'spec/lib/base/struct/Map.spec']);
		preloads:each(action: local Function(String is path){
			local Lexer is plex: Lexer(source: fileRead(path: path, default: ''));
			local Parser is ppar: Parser(tokens: plex:tokenize());
			local ProgramNode is pprog: ppar:parseProgram();
			while([Int is ci: 0], { ci < pprog:classes:length() }, {
				all:push(item: pprog:classes:get(index: ci));
				ci++;
			});
		});
		local Lexer is lx: Lexer(source: src);
		local Parser is p: Parser(tokens: lx:tokenize());
		local ProgramNode is prog: p:parseProgram();
		while([Int is ci: 0], { ci < prog:classes:length() }, {
			all:push(item: prog:classes:get(index: ci));
			ci++;
		});
		while([Int is ci: 0], { ci < all:length() }, {
			local ClassInfo is c: all:get(index: ci);
			Conditional:if(check: { c:baseClasses:length() == 0 && c:baseClass == '' && c:name != 'Any' && c:name != 'Stringable' && c:baseClass != 'Enum' }, then: {
				c:withBaseClasses(name: c:name, baseClasses: ['Any'], members: c:members);
			});
			ci++;
		});
		prog: ProgramNode(classes: all);
		local Array of String is msgs: Array();
		Conditional:if(check: { p:hasErrors() }, then: {
			local [Error] is pErrs: p:getErrors();
			while([Int is pei: 0], { pei < pErrs:length() }, {
				msgs:add(item: pErrs:get(index: pei):getMessage());
				pei++;
			});
			return msgs;
		});
		local TypeChecker is tc: TypeChecker:init();
		local [TypeError] is errs: tc:checkProgram(program: prog);
		local Int is ei: 0;
		while({ ei < errs:length() }, {
			msgs:add(item: errs:get(index: ei):toString());
			ei++;
		});
		return msgs;
	}

	Function is testCleanProgram(){
		local Array of String is e1: :checkOf(src: 'Class is A{ replace Function is init(Map of String to String is args){ local Int is n: 1 + 2 * 3; local Int is m: n + 1; } }');
		Assert:areEqualInt(0, e1:length());
	}

	Function is testBidirectionalEmptyContainers(){
		local Array of String is e2: :checkOf(src: "Class is B{ replace Function is init(Map of String to String is args){ local Array of String is xs: Array(); local Map of String to Int is m: [:]; } }");
		Assert:areEqualInt(0, e2:length());
	}

	Function is testArrayOfXChainedResolution(){
		local Array of String is e3: :checkOf(src: "Class is C{ replace Function is init(Map of String to String is args){ local Array of String is xs: Array(['a', 'b']); local Int is firstLen: xs:get(index: 0):length(); } }");
		Assert:areEqualInt(0, e3:length());
	}

	Function is testTypeMismatchDiagnostic(){
		local Array of String is e4: :checkOf(src: 'Class is D{ replace Function is init(Map of String to String is args){ local Int is n: \'hello\'; } }');
		Assert:areEqualInt(1, e4:length());
		Assert:isTrue(e4:get(index: 0):contains(needle: "cannot assign 'String' to 'Int'"));
	}

	Function is testUndefinedIdentifierDiagnostic(){
		local Array of String is e5: :checkOf(src: 'Class is E{ replace Function is init(Map of String to String is args){ local Int is n: untrackedTotal; } }');
		Assert:isTrue(e5:length() >= 1);
		Assert:isTrue(e5:get(index: 0):contains(needle: "Undefined identifier 'untrackedTotal'"));
	}

	Function is testNonExhaustiveMatchDiagnostic(){
		local Array of String is e6: :checkOf(src: "Enum of String is Level { NONE: '', ERR: 'E' }
Class is F{ replace Array of Array of String is using: [['base', 'sys', as Conditional()]]; replace Function is init(Map of String to String is args){
	local Level is lv: Level:ERR;
	local String is tag: Conditional:match(on: lv, when: [
		Level:ERR: { 'e' }
	]);
} }");
		Assert:isTrue(e6:length() >= 1);
		Assert:isTrue(e6:get(index: 0):contains(needle: 'Non-exhaustive match'));
	}

	Function is testBooleanConditionTyping(){
		local Array of String is e7: :checkOf(src: "Class is G{ replace Array of Array of String is using: [['base', 'sys', as Loops()]]; replace Function is init(Map of String to String is args){ local Int is n: 0; while(evaluate: local Function of Boolean(){ return 1; }, iteration: local Function(){ n: n + 1; }); } }");
		Assert:isTrue(e7:length() > 0);
	}

	Function is testCallResultFieldAccess(){
		local Array of String is e8: :checkOf(src: "Class is Box{ Array of String is items: Array(); Function of Box is make(){ return Box:init(); } }
Class is H{ replace Function is init(Map of String to String is args){
	local Box is made: Box:init();
	local Array of String is xs: made:make():items;
	local Int is n: xs:length();
} }");
		Assert:areEqualInt(0, e8:length());
	}

	Function is testPlainProgramRegression(){
		local Array of String is e9: :checkOf(src: "Class is I{ replace Function is init(Map of String to String is args){ local Int is n: 5; } }\n");
		Assert:areEqualInt(0, e9:length());
	}

	Function is testPrimitiveConversionCasts(){
		local Array of String is e10: :checkOf(src: "Class is J{ replace Function is init(Map of String to String is args){ local Float is f: 3.9; local Int is truncated: f as Int; local Float is widened: 7 as Float; } }");
		Assert:areEqualInt(0, e10:length());
	}

	Function is testUnrelatedClassCastRejected(){
		local Array of String is e11: :checkOf(src: "Class is Cat{ }
Class is Dog{ }
Class is K{ replace Function is init(Map of String to String is args){ local Cat is c: Cat:init(); local Dog is d: c as Dog; } }");
		Assert:isTrue(e11:length() >= 1);
		Assert:isTrue(e11:get(index: 0):contains(needle: "unrelated class"));
	}

	Function is testDeclaredCastViaCastable(){
		local Array of String is e12: :checkOf(src: "Class is L{ replace Function is init(Map of String to String is args){ local String is digits: '1234'; local Int is num: digits as Int; } }");
		Assert:areEqualInt(0, e12:length());
	}

	Function is testCastableReturnTypeMismatch(){
		local Array of String is e13: :checkOf(src: "Class is M{ castable: [[Int, broken]]; Function of String is broken(){ return 'x'; } }
Class is N{ replace Function is init(Map of String to String is args){ local M is m: M:init(); local Int is n: m as Int; } }");
		Assert:isTrue(e13:length() >= 1);
		Assert:isTrue(e13:get(index: 0):contains(needle: "returns 'String', not 'Int'"));
	}

	Function is testMixedPrimitiveArrayRejected(){
		local Array of String is e14: :checkOf(src: "Class is O{ replace Function is init(Map of String to String is args){ local Int is len: [1, 'two']:length(); } }");
		Assert:isTrue(e14:length() >= 1);
		Assert:isTrue(e14:get(index: 0):contains(needle: "Incompatible array element types: 'Int' and 'String'"));
	}

	Function is testUnrelatedClassArrayRejected(){
		local Array of String is e15: :checkOf(src: "Class is Cat{ }
Class is Car{ }
Class is P{ replace Function is init(Map of String to String is args){ local Int is len: [Cat:init(), Car:init()]:length(); } }");
		Assert:isTrue(e15:length() >= 1);
		Assert:isTrue(e15:get(index: 0):contains(needle: "Incompatible array element types: 'Cat' and 'Car'"));
	}

	Function is testSharedParentArrayViaMultipleInheritance(){
		local Array of String is e16: :checkOf(src: "Class is Flyable{ }
Class is Swimmable{ Function of String is swim(){ return 'ok'; } }
Class of Flyable, Swimmable is Duck{ }
Class of Swimmable is Fish{ }
Class is Q{ replace Function is init(Map of String to String is args){
	local Array of Swimmable is swimmers: Array([Duck:init(), Fish:init()]);
	local String is s: [Duck:init(), Fish:init()]:get(index: 0, default: Fish:init()):swim();
} }");
		Assert:areEqualInt(0, e16:length());
	}
}
