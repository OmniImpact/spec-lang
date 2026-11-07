#! Package base:compiler:ast
#! One class definition: identity, inheritance, and members.

Class is ClassInfo{
	namespace: ['base', 'compiler', 'ast'];

	replace Array of Array of String is using: [
		['spec', 'base', 'compiler', 'ast', Member],
		['spec', 'base', 'compiler', 'ast', ExpressionKind]
	];

	## Class identifier.
	String is name: '';

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
		self:baseClasses: if (baseClass != '') [baseClass] else [];
		self:members: members;
	}

	## Initializes a class definition with multiple inheritance.
	##
	## @param name: Class identifier.
	## @param baseClasses: Parent class names.
	## @param members: The class members.
	## The class's declared namespace, joined with ':' ('' when undeclared).
	##
	## @return: The namespace path, e.g. 'base:sysinternal'.
	Function of String is namespaceJoined(){
		local Int is idx: 0;
		While:condition(
			evaluate: local Function of Boolean(){
				return idx < self:members:length();
			},
			iteration: local Function of Boolean(){
				local Member is m: self:members:get(index: idx);
				idx: idx + 1;
				if (m:name == 'namespace' && m:hasInit && m:initExpr:kind == ExpressionKind:ARRAY) {
					local String is joined: '';
					m:initExpr:arrayItems:each(action: local Function(Expression is seg){
						if (joined == '') {
							joined: seg:stringValue;
						} else {
							joined: joined . ':' . seg:stringValue;
						}
					});
					self:nsJoined: joined;
					return false;
				}
				return true;
			}
		);
		return self:nsJoined;
	}

	## Cached [namespaceJoined] result.
	local String is nsJoined: '';

	Function is withBaseClasses(String is name, Array of String is baseClasses, Array of Member is members){
		self:name: name;
		self:baseClasses: baseClasses;
		self:baseClass: if (baseClasses:length() > 0) baseClasses:get(index: 0) else '';
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
