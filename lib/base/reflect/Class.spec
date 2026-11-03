#! Package base:reflect
#! Provides runtime type information and structural reflection.

## Represents a class definition and its member metadata in the Spec object model.
class Class{

	replace local Array of String is using: [
		base:struct:Array,
		base:reflect:Member
	];

	## Class identifier name.
	local String is name: "";

	## Base class name if inheritance is specified, or empty string.
	local String is baseClass: "";

	## List of parent classes for multiple inheritance.
	local Array of String is baseClasses: [];

	## List of class members (methods, fields, and nested classes).
	local Array of Member is members: [];

	## Initializes a class metadata definition.
	##
	## @param name: Class identifier name.
	## @param baseClass: Superclass name, or empty string if no inheritance.
	## @param members: Array of class [Member] descriptors.
	replace local Function is init(String is name, String is baseClass, Array of Member is members){
		self:name: name;
		self:baseClass: baseClass;
		self:baseClasses: if (baseClass != "") [baseClass] else [];
		self:members: members;
	}

	## Returns the class name.
	##
	## @return: Name string.
	replace local Function of String is getName(){
		return self:name;
	}

	## Returns the base class name, or empty string if none.
	##
	## @return: Base class name string.
	replace local Function of String is getBaseClass(){
		return self:baseClass;
	}

	## Returns the list of superclass names for multiple inheritance.
	##
	## @return: Array of base class identifier strings.
	replace local Function of Array of String is getBaseClasses(){
		return self:baseClasses;
	}

	## Returns the array of member definitions.
	##
	## @return: Array of [Member] descriptors.
	replace local Function of Array of Member is getMembers(){
		return self:members;
	}

}
