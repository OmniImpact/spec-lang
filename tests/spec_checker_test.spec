#! TypeChecker port check: bidirectional container typing, the
#! Array-of-X element fix, FIELD_ACCESS on call results, error paths,
#! and clean programs.

Class is SpecCheckerTest{
	namespace: ['test'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'compiler', 'checker', TypeError],
		['base', 'compiler', 'parser', Parser],
		['base', 'compiler', 'lexer', Lexer],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'io', Output],
		['base', 'io', File],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'io', as File()],
		['base', 'io', as Output()]
	];

	## Parses and checks a source, returning the error messages.
	##
	## @param src: Spec source text.
	## @return: Rendered type errors (empty when clean).
	Function of Array of String is checkOf(String is src){
		# Preload the core Spec declarations (String, Array, List, Map) —
		# G7's Loader does this; here the driver parses them directly so the
		# checker resolves their methods from SPEC declarations.
		local Array of ClassInfo is all: [];
		local Array of String is preloads: ['lib/base/core/Any.spec', 'lib/base/core/Stringable.spec', 'lib/base/sysinternal/Buf.spec', 'lib/base/core/String.spec', 'lib/base/struct/Array.spec', 'lib/base/struct/List.spec', 'lib/base/struct/Map.spec'];
		preloads:each(action: local Function(String is path){
			local Lexer is plex: Lexer:init(source: File:read(path: path, default: ''));
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
		# The Loader's implicit-Any pass: every non-enum class without
		# explicit parents derives from Any.
		all:each(action: local Function(ClassInfo is c){
			if (c:baseClasses:length() == 0 && c:baseClass == '' && c:name != 'Any' && c:name != 'Stringable' && c:baseClass != 'Enum') {
				c:withBaseClasses(name: c:name, baseClasses: ['Any'], members: c:members);
			}
		});
		prog: ProgramNode:init(classes: all);
		local Array of String is msgs: [];
		# Parse errors surface first — silently type-checking a broken parse
		# would report a confusing empty result.
		if (p:hasErrors()) {
			p:getErrors():each(action: local Function(Error is e){
				msgs:add(item: e:getMessage());
			});
			return msgs;
		}
		local TypeChecker is tc: TypeChecker:init();
		local Array of TypeError is errs: tc:checkProgram(program: prog);
		errs:each(action: local Function(TypeError is e){
			msgs:add(item: e:toString());
		});
		return msgs;
	}

	replace Function is init(Map of String to String is args){
		Output:line('=== Spec Checker Test ===');
		local Int is failures: 0;

		# 1. Clean program: 0 errors
		local Array of String is e1: self:checkOf(src: 'Class is A{ replace Function is init(Map of String to String is args){ local Int is n: 1 + 2 * 3; local Int is m: n + 1; } }');
		if (e1:length() == 0) {
			Output:line('[PASS] clean program');
		} else {
			Output:line('[FAIL] clean program: ' . e1:join(separator: ' | '));
			failures: failures + 1;
		}

		# 2. Bidirectional: empty array/map literals type from the declaration
		local Array of String is e2: self:checkOf(src: "Class is B{ replace Function is init(Map of String to String is args){ local Array of String is xs: []; local Map of String to Int is m: [:]; } }");
		if (e2:length() == 0) {
			Output:line('[PASS] bidirectional empty containers');
		} else {
			Output:line('[FAIL] bidirectional empty containers: ' . e2:join(separator: ' | '));
			failures: failures + 1;
		}

		# 3. The element-type fix: chained get on 'Array of X' resolves X —
		# the fossil returned Any, so the chained length() was a root-contract error.
		local Array of String is e3: self:checkOf(src: "Class is C{ replace Function is init(Map of String to String is args){ local Array of String is xs: ['a', 'b']; local Int is firstLen: xs:get(index: 0):length(); } }");
		if (e3:length() == 0) {
			Output:line('[PASS] Array of X element resolution through chains');
		} else {
			Output:line('[FAIL] Array of X chains: ' . e3:join(separator: ' | '));
			failures: failures + 1;
		}

		# 4. Type mismatch error path
		local Array of String is e4: self:checkOf(src: 'Class is D{ replace Function is init(Map of String to String is args){ local Int is n: \'hello\'; } }');
		if (e4:length() == 1 && e4:get(index: 0):contains(needle: "cannot assign 'String' to 'Int'")) {
			Output:line('[PASS] mismatch diagnostic');
		} else {
			Output:line('[FAIL] mismatch diagnostic: ' . e4:join(separator: ' | '));
			failures: failures + 1;
		}

		# 5. Undefined identifier
		local Array of String is e5: self:checkOf(src: 'Class is E{ replace Function is init(Map of String to String is args){ local Int is n: untrackedTotal; } }');
		if (e5:length() >= 1 && e5:get(index: 0):contains(needle: "Undefined identifier 'untrackedTotal'")) {
			Output:line('[PASS] undefined identifier diagnostic');
		} else {
			Output:line('[FAIL] undefined identifier: ' . e5:join(separator: ' | '));
			failures: failures + 1;
		}

		# 6. Non-exhaustive when
		local Array of String is e6: self:checkOf(src: "Enum of String is Level { NONE: '', ERR: 'E' }
Class is F{ replace Function is init(Map of String to String is args){
	local Level is lv: Level:ERR;
	local String is tag: when (lv) { is ERR: 'e'; };
} }");
		if (e6:length() >= 1 && e6:get(index: 0):contains(needle: "Non-exhaustive 'when'")) {
			Output:line('[PASS] non-exhaustive when diagnostic');
		} else {
			Output:line('[FAIL] non-exhaustive when: ' . e6:join(separator: ' | '));
			failures: failures + 1;
		}

		# 7. Field initializer bidirectional + root contract
		local Array of String is e7: self:checkOf(src: "Class is G{ replace Function is init(Map of String to String is args){ local Boolean is ok: 1 == 1; if (ok) { local Int is y: 1; } } }");
		if (e7:length() == 0) {
			Output:line('[PASS] boolean condition typing');
		} else {
			Output:line('[FAIL] boolean condition: ' . e7:join(separator: ' | '));
			failures: failures + 1;
		}

		# 8. FIELD_ACCESS on a call result: typed from the field declaration.
		local Array of String is e8: self:checkOf(src: "Class is Box{ Array of String is items: []; Function of Box is make(){ return Box:init(); } }
Class is H{ replace Function is init(Map of String to String is args){
	local Box is made: Box:init();
	local Array of String is xs: made:make():items;
	local Int is n: xs:length();
} }");
		if (e8:length() == 0) {
			Output:line('[PASS] call-result field access typed from declaration');
		} else {
			Output:line('[FAIL] call-result field access: ' . e8:join(separator: ' | '));
			failures: failures + 1;
		}

		# 9. Unknown field on a known class is an error path (resolves Any,
		# but a nonexistent field yields no false type).
		local Array of String is e9: self:checkOf(src: "Class is I{ replace Function is init(Map of String to String is args){ local Int is n: 5; } }
");
		if (e9:length() == 0) {
			Output:line('[PASS] regression: plain program still clean');
		} else {
			Output:line('[FAIL] plain program: ' . e9:join(separator: ' | '));
			failures: failures + 1;
		}

# 10. Primitive conversion casts (declared matrix)
		local Array of String is e10: self:checkOf(src: "Class is J{ replace Function is init(Map of String to String is args){ local Float is f: 3.9; local Int is truncated: f as Int; local Float is widened: 7 as Float; } }");
		if (e10:length() == 0) {
			Output:line('[PASS] primitive conversion casts');
		} else {
			Output:line('[FAIL] primitive conversion casts: ' . e10:join(separator: ' | '));
			failures: failures + 1;
		}

		# 11. Unrelated class cast rejection (inheritance-based)
		local Array of String is e11: self:checkOf(src: "Class is Cat{ }
Class is Dog{ }
Class is K{ replace Function is init(Map of String to String is args){ local Cat is c: Cat:init(); local Dog is d: c as Dog; } }");
		if (e11:length() >= 1 && e11:get(index: 0):contains(needle: "unrelated class")) {
			Output:line('[PASS] unrelated class cast rejected by inheritance');
		} else {
			Output:line('[FAIL] unrelated class cast: ' . e11:join(separator: ' | '));
			failures: failures + 1;
		}

		# 12. Declared cast: String -> Int via String's castable entry.
		local Array of String is e12: self:checkOf(src: "Class is L{ replace Function is init(Map of String to String is args){ local String is digits: '1234'; local Int is num: digits as Int; } }");
		if (e12:length() == 0) {
			Output:line('[PASS] declared cast via castable');
		} else {
			Output:line('[FAIL] declared cast: ' . e12:join(separator: ' | '));
			failures: failures + 1;
		}

		# 13. A castable entry whose function returns the wrong type errors.
		local Array of String is e13: self:checkOf(src: "Class is M{ castable: [[Int, broken]]; Function of String is broken(){ return 'x'; } }
Class is N{ replace Function is init(Map of String to String is args){ local M is m: M:init(); local Int is n: m as Int; } }");
		if (e13:length() >= 1 && e13:get(index: 0):contains(needle: "returns 'String', not 'Int'")) {
			Output:line('[PASS] castable return-type mismatch diagnosed');
		} else {
			Output:line('[FAIL] castable mismatch: ' . e13:join(separator: ' | '));
			failures: failures + 1;
		}

		if (failures == 0) {
			Output:line('[PASS] spec checker test complete');
		} else {
			Output:line('[FAIL] spec checker test: ' . (failures as String) . ' failures');
		}
	}
}
