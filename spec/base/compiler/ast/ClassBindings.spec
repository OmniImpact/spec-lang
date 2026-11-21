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
		['base', 'compiler', 'ast', MemberKind],
		['base', 'compiler', 'ast', Expression],
		['base', 'compiler', 'ast', MetadataField],
		['base', 'compiler', 'lexer', Keyword],
		['base', 'iterator'],
		['base', 'sys', as Loops()]
	];

	## True when the backend must not emit a struct, vtable, or constructor
	## for [c], and the checker must not hold its declarations as call
	## contracts: either the class is a `sysinternal` binding (structural,
	## permanent) or it DECLARES itself a runtime binding with the
	## `binding: true;` metadata field — the declaration travels with the
	## class, replacing the old hardcoded name list (which silently
	## suppressed the emission of any user class sharing a listed name).
	##
	## @param c: The class.
	## @return: true when emission-transparent and contract-free.
	Function of Boolean is isTransparent(ClassInfo is c){
		if({ :isSysinternal(cls: c) }, {
			return true;
		});
		# Ansi is NOT transparent: its sequence builders are real Spec
		# bodies and the size queries delegate to the terminal floor.
		# Loops, Loop, Output, Input, Stderr, File, InputHandler, and
		# Process are NOT transparent either: their methods are the real
		# wrapper bodies composed from the sysinternal floors — their
		# prototypes and definitions emit.
		local Boolean is declared: false;
		local Array of Member is members: c:members;
		local Int is count: members:length();
		local Int is idx: 0;
		while({ !declared && idx < count }, {
			local Member is m: members:get(index: idx);
			idx++;
			if({ m:kind == MemberKind:FIELD && m:name == MetadataField:BINDING:value() && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:BoolLit: local Function(Boolean is v){
						declared: v;
					}
				], default: {});
			});
		});
		return declared;
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
		while(
			[Int is idx: 0],
			{ !isFloor && idx < count },
			{
				local Member is m: members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit }, {
					match(on: m:initExpr, when: [
						Expression:ArrayLit: local Function(Array of Expression is segs){
							if({ segs:length() > 0 }, {
								local Expression is last: segs:get(index: segs:length() - 1);
								local String is lastText: match(on: last, when: [
									Expression:StringLit: local Function of String(String is value){ return value; },
									Expression:Ident: local Function of String(String is name){ return name; },
									else: { '' }
								]);
								if({ lastText == 'sysinternal' }, {
									isFloor: true;
								});
							});
						},
						else: {}
					]);
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
		if({ c:baseClass != 'Enum' }, {
			return false;
		});
		local Boolean is found: false;
		c:members:each(action: local Function(Member is m){
			if({ !found && m:hasModifier(kw: Keyword:HELD) }, {
				found: true;
			});
			# The tagged desugaring: the variants are
			# nested subclasses — the base carries the tag machinery.
			if({ !found && m:kind == MemberKind:CLASS && m:nestedClass:name != '' }, {
				found: true;
			});
		});
		return found;
	}
}
