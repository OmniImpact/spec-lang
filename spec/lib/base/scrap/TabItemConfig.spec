#! Package base:scrap
#! Descriptor for a single tab inside a `TabBar`.

Class is TabItemConfig{
	replace [String] is namespace: ['base', 'scrap'];

	String is id: '';
	String is label: '';
	Boolean is closable: true;
	Boolean is dirty: false;

	replace Function is init(
		String is id: '',
		String is label: '',
		Boolean is closable: true,
		Boolean is dirty: false
	){
		:id: id;
		:label: label;
		:closable: closable;
		:dirty: dirty;
	}
}
