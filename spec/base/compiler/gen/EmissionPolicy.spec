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
## 2. TRANSITIONAL, dies at Phase E: the runtime-managed classes whose
##    instances live in the C runtime (SpecArray*, SpecMap*, ...) and whose
##    declarations are pure API surface. When they are reimplemented in
##    Spec over ByteBuf, this list empties and the method dies.

Class is EmissionPolicy{
	namespace: ['base', 'compiler', 'gen'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', ClassInfo],
		['spec', 'base', 'compiler', 'ast', MetadataField],
		['spec', 'base', 'compiler', 'ast', ExpressionKind],
		['lib', 'base', 'iterator']
	];

	## True when the backend must not emit a struct, vtable, or constructor
	## for [c]: either the class is a `sysinternal` binding (structural,
	## permanent) or its instances are C-runtime-managed (transitional).
	##
	## @param c: The class.
	## @return: true when emission-transparent.
	Function of Boolean is isTransparent(ClassInfo is c){
		if (self:isSysinternal(cls: c)) {
			return true;
		}
		local String is name: c:name;
		return name == 'Array' || name == 'Map' || name == 'File' || name == 'LoopControl' ||
			name == 'Process' || name == 'Output' || name == 'Input' || name == 'Math' ||
			name == 'While' || name == 'Loop' || name == 'LoopCallback' || name == 'InputHandler' ||
			name == 'List' || name == 'String';
	}

	## True when [c]'s namespace ends with the segment `sysinternal` — the
	## namespace is the binding annotation.
	##
	## @param cls: The class.
	## @return: true when the class is a floor binding.
	Function of Boolean is isSysinternal(ClassInfo is cls){
		local SysinternalCheckLoop is check: SysinternalCheckLoop:init(cls: cls);
		While:run(loop: check);
		return check:isFloor;
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
		return !self:isTransparent(c: c) || c:name == 'String';
	}

	## Walks a class's members looking for the namespace declaration and
	## tests whether its last segment is `sysinternal`.
	Class of Loop is SysinternalCheckLoop{
		local ClassInfo is cls;
		local Int is idx: 0;
		local Boolean is isFloor: false;

		replace Function is init(ClassInfo is cls){
			self:cls: cls;
			self:idx: 0;
			self:isFloor: false;
		}

		replace Function of Boolean is evaluate(){
			return self:idx < self:cls:members:length();
		}

		replace Function of Boolean is iteration(LoopControl is control){
			local Member is m: self:cls:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:name == MetadataField:NAMESPACE:value() && m:hasInit) {
				local Expression is nsExpr: m:initExpr;
				if (nsExpr:kind == ExpressionKind:ARRAY) {
					local Array of Expression is items: nsExpr:arrayItems;
					if (items:length() > 0) {
						local Expression is lastExpr: items:get(index: items:length() - 1);
						if (lastExpr:stringValue == 'sysinternal') {
							self:isFloor: true;
							return false;
						}
					}
				}
			}
			return true;
		}
	}
}
