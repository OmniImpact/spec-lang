#! Package specedit:model
#! Pure domain model for SpecEdit (no UI or toolkit dependencies).

Class is EditorModel{
	replace [String] is namespace: ['specedit', 'model'];

	String is filePath: '';
	String is documentName: 'Untitled';
	Boolean is dirty: false;
	String is text: '';

	replace Function is init(String is documentName: 'Untitled'){
		:filePath: '';
		:documentName: documentName;
		dirty: false;
		text: '';
	}
}
