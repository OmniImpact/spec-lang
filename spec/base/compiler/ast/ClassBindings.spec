#! Package base:compiler:ast
#! The shared classification of floor classes.
##
## Two transparency rules, kept separate:
##
## 1. PERMANENT and structural: `sysinternal` classes (namespace ends with
##    the segment `sysinternal`) are interface-style C-floor bindings.
##    Checked by namespace, never by name, so new floor classes need no
##    registration anywhere.
##
## 2. Transitional: the runtime-managed classes whose
##    instances live in the C runtime (SpecArray*, SpecMap*, ...) and whose
##    declarations are pure API surface. When they are reimplemented in
##    Spec over ByteBuf, the list empties and this class shrinks to rule 1.
##
## Lives in the ast package because both the checker (call-site argument
## validation) and the generator (emission decisions) need it — neither
## may own a list the other can drift from.

Class is ClassBindings{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'iterator'],
		['base', 'iterator', as While()]
	];

	## True when the backend must not emit a struct, vtable, or constructor
	## for [c], and the checker must not hold its declarations as call
	## contracts: either the class is a `sysinternal` binding (structural,
	## permanent) or its instances are C-runtime-managed (transitional until the
	## containers are reimplemented over the byte-buffer floor).
	##
	## @param c: The class.
	## @return: true when emission-transparent and contract-free.
	Function of Boolean is isTransparent(ClassInfo is c){
		if (self:isSysinternal(cls: c)) {
			return true;
		}
		# NOTE: names here must be unambiguous across the whole program —
		# a user class sharing a listed name would silently lose its
		# emission. Common names (Error, Token, ...) stay OFF the list;
		# floor singletons like error:line need no class at all.
		local String is name: c:name;
		# Ansi is NOT transparent: its sequence builders are real Spec
		# bodies (only the terminal metrics bind to the ioctl floor).
		return name == 'Array' || name == 'Map' || name == 'File' || name == 'LoopControl' ||
			name == 'Process' || name == 'Output' || name == 'Input' || name == 'Math' ||
			name == 'While' || name == 'Loop' || name == 'LoopCallback' || name == 'InputHandler' ||
			name == 'Parallel' ||
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

	## True when [c]'s instances are compilation-phase data: the AST
	## classes (base:compiler:ast). Their allocation routes to the object
	## arena — refcounts guard aliasing during compilation, and the arena
	## drains the pending field releases and blocks wholesale.
	##
	## @param c: The class.
	## @return: true when arena-allocated.
	Function of Boolean is isArenaType(ClassInfo is c){
		local String is ns: c:namespaceJoined();
		return ns == 'base:compiler:ast';
	}

	## Walks a class's members looking for the namespace declaration and
	## tests whether its last segment is `sysinternal`.
	Class of Loop is SysinternalCheckLoop{

		replace Array of Array of String is using: [
		['base', 'sys', as Conditional()]
		];
		local ClassInfo is cls;
		# The members array is owned at init (a consumption position) so
		# pool eviction inside the iteration cannot free it mid-scan.
		local Array of Member is members: [];
		local Int is idx: 0;
		local Boolean is isFloor: false;

		replace Function is init(ClassInfo is cls){
			self:cls: cls;
			self:members: cls:members;
			self:idx: 0;
			self:isFloor: false;
		}

		replace Function of Boolean is evaluate(){
			return !self:isFloor && self:idx < self:members:length();
		}

		replace Function of Boolean is iteration(LoopControl is c){
			local Member is m: self:members:get(index: self:idx);
			self:idx: self:idx + 1;
			if (m:name == 'namespace' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) {
				local Array of Expression is segs: m:initExpr:arrayItems;
				if (segs:length() > 0) {
					local Expression is last: segs:get(index: segs:length() - 1);
					if (last:stringValue == 'sysinternal') {
						self:isFloor: true;
					}
				}
			}
			return true;
		}
	}
}
