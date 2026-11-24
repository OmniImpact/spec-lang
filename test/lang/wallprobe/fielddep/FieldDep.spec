#! Package wallprobe:fielddep
#! Public-field class for the IV.6 fields-wall negative: the as-import
#! grants FUNCTIONS (and nested-class types), never fields.

Class is FieldDep{
	replace [String] is namespace: ['wallprobe', 'fielddep'];
	String is secretField: 'leaked';

	Function of Int is ok(){
		return 1;
	}
}
