class Member{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Type,
		base:reflect:Parameter,
		base:reflect:Class,
		base:meta:AST
	];

	local String is kind: "";
	local Array of String is modifiers: [];
	local Type is memberType;
	local String is name: "";
	local Array of Parameter is params: [];
	local Array of Statement is body: [];
	local Expression is initExpr;
	local Boolean is hasInit: false;
	local Class is nestedClass;

	replace local Function is init(String is kind){
		self:kind: kind;
	}

	replace local Function is method(Array of String is modifiers, Type is retType, String is name, Array of Parameter is params, Array of Statement is body){
		self:kind: "METHOD";
		self:modifiers: modifiers;
		self:memberType: retType;
		self:name: name;
		self:params: params;
		self:body: body;
	}

	replace local Function is field(Array of String is modifiers, Type is fieldType, String is name, Expression is initExpr, Boolean is hasInit){
		self:kind: "FIELD";
		self:modifiers: modifiers;
		self:memberType: fieldType;
		self:name: name;
		self:initExpr: initExpr;
		self:hasInit: hasInit;
	}

	replace local Function is classMember(Class is nestedClass){
		self:kind: "CLASS";
		self:nestedClass: nestedClass;
	}

	replace local Function of String is getKind(){
		return self:kind;
	}

	replace local Function of String is getName(){
		return self:name;
	}

	replace local Function of Type is getType(){
		return self:memberType;
	}

	replace local Function of Array of String is getModifiers(){
		return self:modifiers;
	}

	replace local Function of Array of Parameter is getParameters(){
		return self:params;
	}

	replace local Function of Array of Statement is getBody(){
		return self:body;
	}

	replace local Function of Expression is getInitExpr(){
		return self:initExpr;
	}

	replace local Function of Boolean is getHasInit(){
		return self:hasInit;
	}

	replace local Function of Class is getNestedClass(){
		return self:nestedClass;
	}

}
