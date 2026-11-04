#! Package base:reflect
#! Provides runtime type information and structural reflection.

## Represents a class definition and its member metadata in the Spec object model.
Class is ClassInfo{

	replace Array of String is using: [
		base:struct:Array,
		base:reflect:Member
	];

	## ClassInfo identifier name.
	local String is name: "";

	## Source line coordinate where this class was declared.
	local Int is line: 0;

	## Source file path where this class was declared.
	local String is sourceFile: "";

	## Base class name if inheritance is specified, or empty string.
	local String is baseClass: "";

	## List of parent classes for multiple inheritance.
	local Array of String is baseClasses: [];

	## Generic type parameter names declared on this class (e.g. ["T"] or ["A", "B"]).
	local Array of String is typeParams: [];

	## List of class members (methods, fields, and nested classes).
	local Array of Member is members: [];

	## Initializes a class metadata definition.
	##
	## @param name: ClassInfo identifier name.
	## @param baseClass: Superclass name, or empty string if no inheritance.
	## @param members: Array of class [Member] descriptors.
	replace Function is init(String is name, String is baseClass, Array of Member is members){
		self:name: name;
		self:baseClass: baseClass;
		self:baseClasses: if (baseClass != "") [baseClass] else [];
		self:members: members;
	}

	## Initializes a class metadata definition with multiple inheritance parents.
	##
	## @param name: ClassInfo identifier name.
	## @param baseClasses: Array of parent class identifier strings.
	## @param members: Array of class [Member] descriptors.
	Function is withBaseClasses(String is name, Array of String is baseClasses, Array of Member is members){
		self:name: name;
		self:baseClasses: baseClasses;
		self:baseClass: if (baseClasses:length() > 0) baseClasses:get(index: 0) else "";
		self:members: members;
	}

	## Returns the class name.
	##
	## @return: Name string.
	Function of String is getName(){
		return self:name;
	}

	## Returns the base class name, or empty string if none.
	##
	## @return: Base class name string.
	Function of String is getBaseClass(){
		return self:baseClass;
	}

	## Returns the list of superclass names for multiple inheritance.
	##
	## @return: Array of base class identifier strings.
	Function of Array of String is getBaseClasses(){
		return self:baseClasses;
	}

	## Returns the array of member definitions.
	##
	## @return: Array of [Member] descriptors.
	Function of Array of Member is getMembers(){
		return self:members;
	}

	## Sets the one-based source line number where this class was declared.
	##
	## @param line: One-based source line number.
	Function is setLine(Int is line){
		self:line: line;
	}

	## Returns the one-based source line number where this class was declared.
	##
	## @return: Source line number.
	Function of Int is getLine(){
		return self:line;
	}

	## Sets the source file path where this class was declared.
	##
	## @param file: Source file path string.
	Function is setSourceFile(String is file){
		self:sourceFile: file;
	}

	## Returns the source file path where this class was declared.
	##
	## @return: Source file path string.
	Function of String is getSourceFile(){
		return self:sourceFile;
	}

	## Sets the generic type parameter names declared on this class.
	##
	## @param params: Array of generic type parameter identifiers.
	Function is setTypeParams(Array of String is params){
		self:typeParams: params;
	}

	## Returns the generic type parameter names declared on this class.
	##
	## @return: Array of generic type parameter identifiers.
	Function of Array of String is getTypeParams(){
		return self:typeParams;
	}

}
