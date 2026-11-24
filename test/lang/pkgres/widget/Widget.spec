#! Package pkgres:widget
#! Fixture for the package-resolution suite test.

Class is Widget{
	replace [String] is namespace: ['pkgres', 'widget'];

	Function of String is speak(){
		return 'widget online';
	}
}
