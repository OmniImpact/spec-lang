#! Package suitshape3d:model
#! Pure domain model for SuitShape3D (app metadata and 3D scene parameters).

Class is Shape3DModel{
	replace [String] is namespace: ['suitshape3d', 'model'];

	String is appName: 'SuitShape3D';
	String is version: '0.1.0';
	String is description: 'Minimal Vulkan 3D spinning cube example';

	replace Function is init(
		String is appName: 'SuitShape3D',
		String is version: '0.1.0',
		String is description: 'Minimal Vulkan 3D spinning cube example'
	){
		:appName: appName;
		:version: version;
		:description: description;
	}
}
