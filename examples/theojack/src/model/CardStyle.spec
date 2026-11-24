#! Package theojack:model
#! Visual card rendering style.

Enum of String is CardStyle{
	replace [String] is namespace: ['theojack', 'model'];

	WIREFRAME: 'Wireframe',
	BLACK: 'Black',
	WHITE: 'White',
	METALLIC: 'Metallic'
}
