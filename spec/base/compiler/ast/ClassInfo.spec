#! Package base:compiler:ast
#! One class definition: identity, inheritance, and members.

Class is ClassInfo{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', Expression],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Shared empty sentinel for read-only default/fallback returns.
	held ClassInfo is EMPTY: ClassInfo(name: '', baseClass: '', members: []);

	## Class identifier.
	String is name: '';

	## the qualified enclosing-class chain for a
	## nested (inner) class — 'Outer' or 'Outer:Mid'; '' for top-level
	## classes. The parent link rides baseClasses (the outer's bare name is
	## appended at parse time), so the standard lattice walks — the bare
	## scope, the §I.6 gating, the member lookup — serve inner classes
	## without special cases.
	String is outerName: '';

	## One-based source line where the class was declared.
	Int is line: 0;

	## Source file where the class was declared.
	String is sourceFile: '';

	## Primary parent class name (empty when none).
	String is baseClass: '';

	## All parent class names (multiple inheritance).
	[String] is baseClasses: [];

	## Generic type parameter names declared on the class (e.g. T).
	[String] is typeParams: [];

	## Class members (methods, fields, nested classes).
	[Member] is members: [];

	## Initializes a class definition with single inheritance.
	##
	## @param name: Class identifier.
	## @param baseClass: Parent class name (empty when none).
	## @param members: The class members.
	replace Function is init(String is name, String is baseClass, [Member] is members){
		:name: name;
		:baseClass: baseClass;
		:baseClasses: if({ baseClass != '' }, { [baseClass] }, { [] });
		:members: members;
	}

	## Initializes a class definition with multiple inheritance.
	##
	## @param name: Class identifier.
	## @param baseClasses: Parent class names.
	## @param members: The class members.
	## True when this class's using declaration instance-imports [name]
	## via the as-form (§2.1): a using entry terminating in
	## `as Name()` materializes an owned instance whose members answer to
	## the class-name prefix.
	##
	## @param name: Class name to test.
	## @return: true when an as-form entry names [name].
	Function of Boolean is instanceImportsAs(String is name){
		local Boolean is found: false;
		while([Int is mi: 0], { !found && mi < :members:length() }, {
			local Member is m: :members:get(index: mi);
			if({ m:name == 'using' && m:hasInit }, {
				match(on: m:initExpr, when: [
					Expression:ArrayLit: local Function([Expression] is items){
						while([Int is ii: 0], { !found && ii < items:length() }, {
							match(on: items:get(index: ii), when: [
								Expression:ArrayLit: local Function([Expression] is subItems){
									while([Int is si: 0], { !found && si < subItems:length() }, {
										local Expression is seg: subItems:get(index: si);
										match(on: seg, when: [
											Expression:UsingAs: local Function(String is className, [NamedArg] is args){
												if({ className == name && seg:usingAsAlias == '' }, {
													found: true;
												});
											},
											else: {}
										]);
										si++;
									});
								},
								else: {}
							]);
							ii++;
						});
					},
					else: {}
				]);
			});
			mi++;
		});
		return found;
	}

	## The class's declared namespace, joined with ':' ('' when undeclared).
	##
	## @return: The namespace path, e.g. 'base:sysinternal'.
	Function of String is namespaceJoined(){
		local String is joined: '';
		local Int is count: :members:length();
		while(
			[Int is idx: 0],
			{ joined == '' && idx < count },
			{
				local Member is m: :members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit }, {
					match(on: m:initExpr, when: [
						Expression:ArrayLit: local Function([Expression] is items){
							while([Int is ii: 0], { ii < items:length() }, {
								local Expression is seg: items:get(index: ii);
								local String is segText: match(on: seg, when: [
									Expression:StringLit: local Function of String(String is value){ return value; },
									Expression:Ident: local Function of String(String is name){ return name; },
									else: { '' }
								]);
								if({ joined == '' }, {
									joined: segText;
								}, {
									joined: joined . ':' . segText;
								});
								ii++;
							});
						},
						else: {}
					]);
				});
			}
		);
		return joined:copy();
	}

	## The class's declared namespace as its segment array (empty when
	## undeclared) — the structural form the discipline checks compare.
	## Segment comparison separates `base:sys` (and its sub-packages)
	## from `base:sysinternal` exactly; a prefix test on the joined
	## string conflates them.
	##
	## @return: The namespace segments, e.g. ['base', 'sysinternal'].
	Function of Array of String is namespaceSegments(){
		local Array of String is segs: Array();
		local Int is count: :members:length();
		while(
			[Int is idx: 0],
			{ segs:length() == 0 && idx < count },
			{
				local Member is m: :members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit }, {
					match(on: m:initExpr, when: [
						Expression:ArrayLit: local Function([Expression] is items){
							while([Int is ii: 0], { ii < items:length() }, {
								local Expression is seg: items:get(index: ii);
								local String is segText: match(on: seg, when: [
									Expression:StringLit: local Function of String(String is value){ return value; },
									Expression:Ident: local Function of String(String is name){ return name; },
									else: { '' }
								]);
								segs:add(item: segText);
								ii++;
							});
						},
						else: {}
					]);
				});
			}
		);
		return segs;
	}

	## records the qualified enclosing chain.
	##
	## @param name: 'Outer' or 'Outer:Mid'.
	## true when [member] is declared directly
	## by THIS class (identity compare) — as opposed to inherited through
	## the base lattice. The constructor emission uses it to run the
	## construction expressions for own fields only; inherited fields
	## start empty on inner instances.
	##
	## @param member: The flattened-field member.
	## @return: true when declared by this class.
	Function of Boolean is declaresMember(Member is member){
		local Boolean is found: false;
		while([Int is mi: 0], { !found && mi < :members:length() }, {
			if({ :members:get(index: mi) == member }, {
				found: true;
			});
			mi++;
		});
		return found;
	}

	## the qualified identity — the outer chain
	## + the bare name ('Outer:Helper'); the bare name for top-level
	## classes. The C symbol base and the registry key derive from this.
	##
	## @return: The qualified class name.
	Function of String is qualifiedName(){
		if({ :outerName != '' }, {
			return :outerName . ':' . :name;
		});
		return :name;
	}

	Function is setOuter(String is name){
		:outerName: name;
	}

	Function is withBaseClasses(String is name, [String] is baseClasses, [Member] is members){
		:name: name;
		:baseClasses: baseClasses;
		:baseClass: if({ baseClasses:length() > 0 }, { baseClasses:get(index: 0) }, { '' });
		:members: members;
	}

	## Sets the generic type parameter names.
	##
	## @param params: Generic parameter identifiers.
	Function is setTypeParams([String] is params){
		:typeParams: params;
	}

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function is setLine(Int is line){
		:line: line;
	}

	## Sets the declaring source file.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		:sourceFile: file;
	}
}
