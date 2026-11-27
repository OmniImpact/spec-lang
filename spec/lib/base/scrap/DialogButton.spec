#! Package base:scrap
#! Button descriptor (title, description tooltip, primary flag, and click callback) for generic [Dialog:compose] windows.

Class is DialogButton{
	replace [String] is namespace: ['base', 'scrap'];

	String is title: 'OK';
	String is description: '';
	Boolean is primary: false;
	Function is onClick: local Function(){};

	replace Function is init(
		String is title: 'OK',
		String is description: '',
		Boolean is primary: false,
		Function is onClick: local Function(){}
	){
		:title: title;
		:description: description;
		:primary: primary;
		:onClick: onClick;
	}
}
