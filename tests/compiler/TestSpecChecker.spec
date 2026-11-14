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
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'sys', File],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as File()],
		['base', 'sys', as Conditional()]
	];

	## Parses and checks a source, returning the error messages.
	##
	## @param src: Spec source text.
	## @return: Rendered type errors (empty when clean).
	Function of Array of String is checkOf(String is src){
		local Array of ClassInfo is all: [];
		local Array of String is preloads: ['lib/base/core/Any.spec', 'lib/base/core/Stringable.spec', 'lib/base/sysinternal/Buf.spec', 'lib/base/core/String.spec', 'lib/base/struct/Array.spec', 'lib/base/struct/List.spec', 'lib/base/struct/Map.spec', 'spec/lib/base/sys/Conditional.spec'];
		preloads:each(action: local Function(String is path){
			local Lexer is plex: Lexer:init(source: fileRead(path: path, default: ''));
			local Parser is ppar: Parser:init(tokens: plex:tokenize());
			local ProgramNode is pprog: ppar:parseProgram();
			pprog:classes:each(action: local Function(ClassInfo is c){
				all:add(item: c);
			});
		});
		local Lexer is lx: Lexer:init(source: src);
		local Parser is p: Parser:init(tokens: lx:tokenize());
		local ProgramNode is prog: p:parseProgram();
		prog:classes:each(action: local Function(ClassInfo is c){
			all:add(item: c);
		});
		all:each(action: local Function(ClassInfo is c){
			Conditional:if(check: { c:baseClasses:length() == 0 && c:baseClass == '' && c:name != 'Any' && c:name != 'Stringable' && c:baseClass != 'Enum' }, then: {
				c:withBaseClasses(name: c:name, baseClasses: ['Any'], members: c:members);
			});
		});
		prog: ProgramNode:init(classes: all);
		local Array of String is msgs: [];
		Conditional:if(check: { p:hasErrors() }, then: {
			p:getErrors():each(action: local Function(Error is e){
				msgs:add(item: e:getMessage());
			});
			return msgs;
		});
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errs: tc:checkProgram(program: prog);
		errs:each(action: local Function(TypeError is e){
			msgs:add(item: e:toString());
		});
		return msgs;
	}

	Function is testCleanProgram(){
		local Array of String is e1: self:checkOf(src: 'Class is A{ replace Function is init(Map of String to String is args){ local Int is n: 1 + 2 * 3; local Int is m: n + 1; } }');
		Assert:areEqualInt(0, e1:length());
	}

	Function is testBidirectionalEmptyContainers(){
		local Array of String is e2: self:checkOf(src: "Class is B{ replace Function is init(Map of String to String is args){ local Array of String is xs: []; local Map of String to Int is m: [:]; } }");
		Assert:areEqualInt(0, e2:length());
	}

	Function is testArrayOfXChainedResolution(){
		local Array of String is e3: self:checkOf(src: "Class is C{ replace Function is init(Map of String to String is args){ local Array of String is xs: ['a', 'b']; local Int is firstLen: xs:get(index: 0):length(); } }");
		Assert:areEqualInt(0, e3:length());
	}

	Function is testTypeMismatchDiagnostic(){
		local Array of String is e4: self:checkOf(src: 'Class is D{ replace Function is init(Map of String to String is args){ local Int is n: \'hello\'; } }');
		Assert:areEqualInt(1, e4:length());
		Assert:isTrue(e4:get(index: 0):contains(needle: "cannot assign 'String' to 'Int'"));
	}

	Function is testUndefinedIdentifierDiagnostic(){
		local Array of String is e5: self:checkOf(src: 'Class is E{ replace Function is init(Map of String to String is args){ local Int is n: untrackedTotal; } }');
		Assert:isTrue(e5:length() >= 1);
		Assert:isTrue(e5:get(index: 0):contains(needle: "Undefined identifier 'untrackedTotal'"));
	}

	Function is testNonExhaustiveMatchDiagnostic(){
		local Array of String is e6: self:checkOf(src: "Enum of String is Level { NONE: '', ERR: 'E' }
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
		local Array of String is e7: self:checkOf(src: "Class is G{ replace Array of Array of String is using: [['base', 'sys', as Loops()]]; replace Function is init(Map of String to String is args){ local Int is n: 0; while(evaluate: local Function of Boolean(){ return 1; }, iteration: local Function(){ n: n + 1; }); } }");
		Assert:isTrue(e7:length() > 0);
	}

	Function is testCallResultFieldAccess(){
		local Array of String is e8: self:checkOf(src: "Class is Box{ Array of String is items: []; Function of Box is make(){ return Box:init(); } }
Class is H{ replace Function is init(Map of String to String is args){
	local Box is made: Box:init();
	local Array of String is xs: made:make():items;
	local Int is n: xs:length();
} }");
		Assert:areEqualInt(0, e8:length());
	}

	Function is testPlainProgramRegression(){
		local Array of String is e9: self:checkOf(src: "Class is I{ replace Function is init(Map of String to String is args){ local Int is n: 5; } }\n");
		Assert:areEqualInt(0, e9:length());
	}

	Function is testPrimitiveConversionCasts(){
		local Array of String is e10: self:checkOf(src: "Class is J{ replace Function is init(Map of String to String is args){ local Float is f: 3.9; local Int is truncated: f as Int; local Float is widened: 7 as Float; } }");
		Assert:areEqualInt(0, e10:length());
	}

	Function is testUnrelatedClassCastRejected(){
		local Array of String is e11: self:checkOf(src: "Class is Cat{ }
Class is Dog{ }
Class is K{ replace Function is init(Map of String to String is args){ local Cat is c: Cat:init(); local Dog is d: c as Dog; } }");
		Assert:isTrue(e11:length() >= 1);
		Assert:isTrue(e11:get(index: 0):contains(needle: "unrelated class"));
	}

	Function is testDeclaredCastViaCastable(){
		local Array of String is e12: self:checkOf(src: "Class is L{ replace Function is init(Map of String to String is args){ local String is digits: '1234'; local Int is num: digits as Int; } }");
		Assert:areEqualInt(0, e12:length());
	}

	Function is testCastableReturnTypeMismatch(){
		local Array of String is e13: self:checkOf(src: "Class is M{ castable: [[Int, broken]]; Function of String is broken(){ return 'x'; } }
Class is N{ replace Function is init(Map of String to String is args){ local M is m: M:init(); local Int is n: m as Int; } }");
		Assert:isTrue(e13:length() >= 1);
		Assert:isTrue(e13:get(index: 0):contains(needle: "returns 'String', not 'Int'"));
	}

	Function is testMixedPrimitiveArrayRejected(){
		local Array of String is e14: self:checkOf(src: "Class is O{ replace Function is init(Map of String to String is args){ local Int is len: [1, 'two']:length(); } }");
		Assert:isTrue(e14:length() >= 1);
		Assert:isTrue(e14:get(index: 0):contains(needle: "Incompatible array element types: 'Int' and 'String'"));
	}

	Function is testUnrelatedClassArrayRejected(){
		local Array of String is e15: self:checkOf(src: "Class is Cat{ }
Class is Car{ }
Class is P{ replace Function is init(Map of String to String is args){ local Int is len: [Cat:init(), Car:init()]:length(); } }");
		Assert:isTrue(e15:length() >= 1);
		Assert:isTrue(e15:get(index: 0):contains(needle: "Incompatible array element types: 'Cat' and 'Car'"));
	}

	Function is testSharedParentArrayViaMultipleInheritance(){
		local Array of String is e16: self:checkOf(src: "Class is Flyable{ }
Class is Swimmable{ Function of String is swim(){ return 'ok'; } }
Class of Flyable, Swimmable is Duck{ }
Class of Swimmable is Fish{ }
Class is Q{ replace Function is init(Map of String to String is args){
	local Array of Swimmable is swimmers: [Duck:init(), Fish:init()];
	local String is s: [Duck:init(), Fish:init()]:get(index: 0, default: Fish:init()):swim();
} }");
		Assert:areEqualInt(0, e16:length());
	}
}
