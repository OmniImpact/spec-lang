#! Package base:scrap
#! Generic tree item model for [TreeView].

Class is TreeNode{
	replace [String] is namespace: ['base', 'scrap', 'tree'];

	replace [[String]] is using: [
		['base', 'struct', Array]
	];

	String is id: '';
	String is label: '';
	Boolean is expandable: false;
	Boolean is expanded: false;
	Boolean is loaded: false;
	Array of TreeNode is children: Array();

	replace Function is init(
		String is id: '',
		String is label: '',
		Boolean is expandable: false,
		Boolean is expanded: false,
		Boolean is loaded: false,
		Array of TreeNode is children: Array()
	){
		:id: id;
		:label: label;
		:expandable: expandable;
		:expanded: expanded;
		:loaded: loaded;
		:children: children;
	}
}
