#! Package base:cli
#! Metadata for a single CLI option parsed from a bundled JSON schema.

Class is CliOption{
	replace [String] is namespace: ['base', 'cli'];

	replace [[String]] is using: [
		['base', 'sys', as Conditional()]
	];

	String is shortName: '';
	String is longName: '';
	String is optType: 'string';
	String is defaultVal: '';
	String is argLabel: '';
	String is description: '';
	Boolean is required: false;

	replace Function is init(
		String is shortName: '',
		String is longName: '',
		String is optType: 'string',
		String is defaultVal: '',
		String is argLabel: '',
		String is description: '',
		Boolean is required: false
	){
		:shortName: shortName;
		:longName: longName;
		:optType: optType;
		:defaultVal: defaultVal;
		:argLabel: argLabel;
		:description: description;
		:required: required;
	}

	Function of String is canonicalKey(){
		if({ longName != '' }, { return longName; });
		return shortName;
	}
}
