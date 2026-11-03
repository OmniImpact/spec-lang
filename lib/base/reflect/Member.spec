#! Package base:reflect
#! Provides runtime type information and structural reflection.

Enum is MemberKind {
	METHOD,
	FIELD,
	CLASS,
	ENUM
}

## Represents a field, method, or nested class member definition on a [Class].
class Member{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Class,
		base:meta:AST
	];

	## Member kind tag: "METHOD", "FIELD", or "CLASS".
	local String is kind: "";

	## Source line coordinate where this member was declared.
	local Int is line: 0;

	## Modifiers attached to this member (e.g. `["replace", "local"]`).
	local Array of String is modifiers: [];

	## Return type for methods, or value type for fields.
	local Type is memberType;

	## Identifier name of the member.
	local String is name: "";

	## Formal parameter list for methods.
	local Array of Parameter is params: [];

	## Implementation statements body for methods.
	local Array of Statement is body: [];

	## Initializer expression for fields.
	local Expression is initExpr;

	## Flag indicating if field has an explicit initializer.
	local Boolean is hasInit: false;

	## Nested class descriptor if member kind is "CLASS".
	local Class is nestedClass;

	## Initializes a member descriptor with a kind tag.
	##
	## @param kind: Member kind tag ("METHOD", "FIELD", or "CLASS").
	replace local Function is init(String is kind){
		self:kind: kind;
	}

	## Configures this member as a method definition.
	##
	## @param modifiers: Access and dispatch modifiers.
	## @param retType: Return [Type] descriptor.
	## @param name: Method name.
	## @param params: Method parameter definitions.
	## @param body: Array of [Statement] AST nodes.
	replace local Function is method(Array of String is modifiers, Type is retType, String is name, Array of Parameter is params, Array of Statement is body){
		self:kind: "METHOD";
		self:modifiers: modifiers;
		self:memberType: retType;
		self:name: name;
		self:params: params;
		self:body: body;
	}

	## Configures this member as a field definition.
	##
	## @param modifiers: Field modifiers.
	## @param fieldType: Field [Type] descriptor.
	## @param name: Field identifier name.
	## @param initExpr: Optional initializer [Expression].
	## @param hasInit: `true` if an initializer was provided.
	replace local Function is field(Array of String is modifiers, Type is fieldType, String is name, Expression is initExpr, Boolean is hasInit){
		self:kind: "FIELD";
		self:modifiers: modifiers;
		self:memberType: fieldType;
		self:name: name;
		self:initExpr: initExpr;
		self:hasInit: hasInit;
	}

	## Configures this member as a nested class.
	##
	## @param nestedClass: Nested [Class] descriptor.
	replace local Function is classMember(Class is nestedClass){
		self:kind: "CLASS";
		self:nestedClass: nestedClass;
	}

	## Returns the member kind ("METHOD", "FIELD", or "CLASS").
	##
	## @return: Kind tag string.
	replace local Function of String is getKind(){
		return self:kind;
	}

	## Returns the member kind enum variant.
	##
	## @return: [MemberKind] variant.
	replace local Function of MemberKind is getMemberKind(){
		return when (self:kind) {
			is "METHOD": MemberKind:METHOD;
			is "CLASS": MemberKind:CLASS;
			is "ENUM": MemberKind:ENUM;
			else: MemberKind:FIELD;
		};
	}

	## Returns the member name.
	##
	## @return: Member name string.
	replace local Function of String is getName(){
		return self:name;
	}

	## Returns the type descriptor (return type for methods, value type for fields).
	##
	## @return: [Type] instance.
	replace local Function of Type is getType(){
		return self:memberType;
	}

	## Returns the list of modifiers.
	##
	## @return: Array of modifier strings.
	replace local Function of Array of String is getModifiers(){
		return self:modifiers;
	}

	## Returns the parameter definitions for methods.
	##
	## @return: Array of [Parameter] descriptors.
	replace local Function of Array of Parameter is getParameters(){
		return self:params;
	}

	## Returns the implementation body statements for methods.
	##
	## @return: Array of [Statement] AST nodes.
	replace local Function of Array of Statement is getBody(){
		return self:body;
	}

	## Returns the field initializer expression if present.
	##
	## @return: Initializer [Expression] instance.
	replace local Function of Expression is getInitExpr(){
		return self:initExpr;
	}

	## Indicates whether this field has an explicit initializer.
	##
	## @return: `true` if initialized, `false` otherwise.
	replace local Function of Boolean is getHasInit(){
		return self:hasInit;
	}

	## Returns the nested class definition if kind is "CLASS".
	##
	## @return: [Class] descriptor.
	replace local Function of Class is getNestedClass(){
		return self:nestedClass;
	}

	replace local Function is setLine(Int is line){
		self:line: line;
	}

	replace local Function of Int is getLine(){
		return self:line;
	}

}
