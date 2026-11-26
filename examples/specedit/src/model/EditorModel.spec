#! Package specedit:model
#! Pure domain model for SpecEdit (no UI or toolkit dependencies).

Class is EditorModel{
	replace [String] is namespace: ['specedit', 'model'];

	replace [[String]] is using: [
		['specedit', 'util', SpecEditStrings]
	];

	String is filePath: '';
	String is documentName: SpecEditStrings:UNTITLED;
	Boolean is dirty: false;
	String is text: '';
	String is languageOverride: '';

	replace Function is init(String is documentName: SpecEditStrings:UNTITLED){
		:filePath: '';
		:documentName: documentName;
		dirty: false;
		text: '';
		languageOverride: '';
	}
}
