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
		['base', 'sys', as Conditional()],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator'],
		['base', 'sys', as Loops()]
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
		Conditional:if(check: { self:isSysinternal(cls: c) }, then: {
			return true;
		});
		# NOTE: names here must be unambiguous across the whole program —
		# a user class sharing a listed name would silently lose its
		# emission. Common names (Error, Token, ...) stay OFF the list;
		# floor singletons like error:line need no class at all.
		local String is name: c:name;
		# Ansi is NOT transparent: its sequence builders are real Spec
		# bodies and the size queries delegate to the terminal floor.
		# Loops, Loop, Output, Input, Stderr, File, InputHandler, and
		# Process are NOT transparent either: their methods are the real
		# wrapper bodies composed from the sysinternal floors — their
		# prototypes and definitions emit.
		return name == 'Array' || name == 'Map' || name == 'LoopControl' ||
			name == 'Math' ||
			name == 'LoopCallback' ||
			name == 'Parallel' ||
			name == 'List' || name == 'String';
	}

	## True when [c]'s namespace ends with the segment `sysinternal` — the
	## namespace is the binding annotation.
	##
	## @param cls: The class.
	## @return: true when the class is a floor binding.
	Function of Boolean is isSysinternal(ClassInfo is cls){
		local Boolean is isFloor: false;
		local Array of Member is members: cls:members;
		local Int is count: members:length();
		Loops(
			[Int is idx: 0],
			{ !isFloor && idx < count },
			{
				local Member is m: members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, {
					local Array of Expression is segs: m:initExpr:arrayItems;
					if({ segs:length() > 0 }, {
						local Expression is last: segs:get(index: segs:length() - 1);
						if({ last:str == 'sysinternal' }, {
							isFloor: true;
						});
					});
				});
			}
		);
		return isFloor;
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

	## True when an Enum-rooted class is CLASS-MODEL:
	## it declares held members — the variants are class instances, not
	## int tags — so every today's-enum path (the int-enum emission, the
	## variant registries, the tag accessors) must leave it alone and
	## the class paths (struct, vtable, constructor, held slots) apply.
	## The marker is held members: the sugar's variants carry the
	## hardcoded ['static','local'] tags and can never be held. The
	## base class is compared by name (the checker's enumHeader()) —
	## an 'Enum' class declaration is the only route to it.
	##
	## @param c: The class.
	## @return: true when Enum-rooted with held members.
	Function of Boolean is isClassModelEnum(ClassInfo is c){
		Conditional:if(check: { c:baseClass != 'Enum' }, then: {
			return false;
		});
		local Boolean is found: false;
		c:members:each(action: local Function(Member is m){
			Conditional:if(check: { !found && m:hasModifier(kw: Keyword:HELD) }, then: {
				found: true;
			});
			# The tagged desugaring: the variants are
			# nested subclasses — the base carries the tag machinery.
			Conditional:if(check: { !found && m:kind == MemberKind:CLASS && m:nestedClass:name != '' }, then: {
				found: true;
			});
		});
		return found;
	}
}
