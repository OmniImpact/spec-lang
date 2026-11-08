#! Package base:compiler:checker:loops
#! Resolves a field-access path segment by segment, walking field types
## through the class hierarchy. Stops when the current type is an enum
## (variants are not fields) or a segment resolves to nothing.

Class of Loop is PathResolveLoop{
	namespace: ['base', 'compiler', 'checker', 'loops'];

	replace Array of Array of String is using: [
		['base', 'compiler', 'checker', TypeChecker],
		['base', 'sys', as Conditional()]
	];

	local TypeChecker is tc;
	local Array of String is segs;
	local Int is idx: 1;
	local String is currType: '';

	replace Function is init(TypeChecker is tc, Array of String is segs, String is rootType){
		self:tc: tc;
		self:segs: segs;
		self:currType: rootType;
		self:idx: 1;
	}

	replace Function of Boolean is evaluate(){
		return self:currType != '' && self:idx < self:segs:length();
	}

	replace Function of Boolean is iteration(LoopControl is c){
		local String is seg: self:segs:get(index: self:idx);
		self:idx: self:idx + 1;
		if (self:tc:allEnumNames:has(key: self:currType)) {
			return true;
		}
		self:currType: self:tc:lookupFieldType(className: self:currType, fieldName: seg);
		return true;
	}
}
