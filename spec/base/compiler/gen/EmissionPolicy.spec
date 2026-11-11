#! Package base:compiler:gen
#! Decides what the backend emits for a class.
##
## Two transparency rules, kept separate:
##
## 1. PERMANENT and structural: `sysinternal` classes (namespace ends with
##    the segment `sysinternal`) are interface-style bindings — no struct,
##    no vtable, no constructor is ever emitted for them. Checked by
##    namespace, never by name, so new floor classes need no registration.
##
## 2. Transitional: the runtime-managed classes whose
##    instances live in the C runtime (SpecArray*, SpecMap*, ...) and whose
##    declarations are pure API surface. When they are reimplemented in
##    Spec over ByteBuf, this list empties and the method dies.

Class is EmissionPolicy{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', ClassBindings],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'iterator']
	];

	## The shared floor-class classification.
	local ClassBindings is bindings: ClassBindings:init();

	## True when the backend must not emit a struct, vtable, or constructor
	## for [c]. Delegates to the shared classification (ast.ClassBindings) —
	## the checker reads the same decision for call-site validation.
	##
	## @param c: The class.
	## @return: true when emission-transparent.
	Function of Boolean is isTransparent(ClassInfo is c){
		local ClassBindings is b: self:bindings;
		return b:isTransparent(c: c);
	}

	## True when [c]'s namespace ends with the segment `sysinternal`.
	##
	## @param cls: The class.
	## @return: true when the class is a floor binding.
	Function of Boolean is isSysinternal(ClassInfo is cls){
		local ClassBindings is b: self:bindings;
		return b:isSysinternal(cls: cls);
	}

	## True when the backend emits real C functions for the class's methods
	## even though its representation is runtime-managed ([String] is the
	## case: direct-dispatched Spec bodies over the floor). sysinternal
	## bindings never get prototypes — their C functions are prelude
	## declarations, not per-class methods.
	##
	## @param c: The class.
	## @return: true when method prototypes are emitted.
	Function of Boolean is emitsPrototypes(ClassInfo is c){
		return !self:isTransparent(c: c) || c:name == 'String' || c:name == 'Array' || c:name == 'Map';
	}

	## True when [c]'s instances are compilation-phase data: the AST
	## classes (base:compiler:ast).
	##
	## @param c: The class.
	## @return: true when arena-allocated.
	Function of Boolean is isArenaType(ClassInfo is c){
		return self:bindings:isArenaType(c: c);
	}

	## True when an Enum-rooted class is CLASS-MODEL:
	## held members make the variants class instances — every today's-
	## enum emission path must leave it alone. Delegates to the shared
	## classification the checker reads too.
	##
	## @param c: The class.
	## @return: true when Enum-rooted with held members.
	Function of Boolean is isClassModelEnum(ClassInfo is c){
		return self:bindings:isClassModelEnum(c: c);
	}
}
