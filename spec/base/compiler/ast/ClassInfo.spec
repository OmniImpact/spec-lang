#! Package base:compiler:ast
#! One class definition: identity, inheritance, and members.

Class is ClassInfo{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'ast', Member],
		['base', 'sys', as Buf()],
		['base', 'compiler', 'ast', ExpressionKind],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

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
	Array of String is baseClasses: [];

	## Generic type parameter names declared on the class (e.g. T).
	Array of String is typeParams: [];

	## Class members (methods, fields, nested classes).
	Array of Member is members: [];

	## Initializes a class definition with single inheritance.
	##
	## @param name: Class identifier.
	## @param baseClass: Parent class name (empty when none).
	## @param members: The class members.
	replace Function is init(String is name, String is baseClass, Array of Member is members){
		self:name: name;
		self:baseClass: baseClass;
		self:baseClasses: Conditional:if(check: { baseClass != '' }, then: { [baseClass] }, else: { [] });
		self:members: members;
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
		self:members:each(action: local Function(Member is m){
			Conditional:if(check: { !found && m:name == 'using' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, then: {
				m:initExpr:arrayItems:each(action: local Function(Expression is item){
					Conditional:if(check: { item:kind == ExpressionKind:ARRAY }, then: {
						item:arrayItems:each(action: local Function(Expression is seg){
							Conditional:if(check: { seg:kind == ExpressionKind:USING_AS && seg:str == name }, then: {
								found: true;
							});
						});
					});
				});
			});
		});
		return found;
	}

	## The class's declared namespace, joined with ':' ('' when undeclared).
	##
	## @return: The namespace path, e.g. 'base:sysinternal'.
	Function of String is namespaceJoined(){
		local String is joined: '';
		local Int is count: self:members:length();
		Loops(
			[Int is idx: 0],
			{ joined == '' && idx < count },
			{
				local Member is m: self:members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, {
					m:initExpr:arrayItems:each(action: local Function(Expression is seg){
						if({ joined == '' }, {
							joined: seg:str;
						}, {
							joined: joined . ':' . seg:str;
						});
					});
				});
			}
		);
		return Buf:stringCopy(b: joined);
	}

	## The class's declared namespace as its segment array (empty when
	## undeclared) — the structural form the discipline checks compare.
	## Segment comparison separates `base:sys` (and its sub-packages)
	## from `base:sysinternal` exactly; a prefix test on the joined
	## string conflates them.
	##
	## @return: The namespace segments, e.g. ['base', 'sysinternal'].
	Function of Array of String is namespaceSegments(){
		local Array of String is segs: [];
		local Int is count: self:members:length();
		Loops(
			[Int is idx: 0],
			{ segs:length() == 0 && idx < count },
			{
				local Member is m: self:members:get(index: idx);
				idx++;
				if({ m:name == 'namespace' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY }, {
					m:initExpr:arrayItems:each(action: local Function(Expression is seg){
						segs:add(item: seg:str);
					});
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
		self:members:each(action: local Function(Member is m){
			Conditional:if(check: { !found && m == member }, then: {
				found: true;
			});
		});
		return found;
	}

	## the qualified identity — the outer chain
	## + the bare name ('Outer:Helper'); the bare name for top-level
	## classes. The C symbol base and the registry key derive from this.
	##
	## @return: The qualified class name.
	Function of String is qualifiedName(){
		Conditional:if(check: { self:outerName != '' }, then: {
			return self:outerName . ':' . self:name;
		});
		return self:name;
	}

	Function is setOuter(String is name){
		self:outerName: name;
	}

	Function is withBaseClasses(String is name, Array of String is baseClasses, Array of Member is members){
		self:name: name;
		self:baseClasses: baseClasses;
		self:baseClass: Conditional:if(check: { baseClasses:length() > 0 }, then: { baseClasses:get(index: 0) }, else: { '' });
		self:members: members;
	}

	## Sets the generic type parameter names.
	##
	## @param params: Generic parameter identifiers.
	Function is setTypeParams(Array of String is params){
		self:typeParams: params;
	}

	## Sets the one-based source line.
	##
	## @param line: Source line number.
	Function is setLine(Int is line){
		self:line: line;
	}

	## Sets the declaring source file.
	##
	## @param file: Source file path.
	Function is setSourceFile(String is file){
		self:sourceFile: file;
	}
}
