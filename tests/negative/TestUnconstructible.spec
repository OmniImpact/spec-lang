#! --test suite rule: test classes construct with no arguments (the
#! reflection runner instantiates them through the registry's
#! zero-argument constructor). An init that requires arguments is a
#! compile-time diagnostic.

Class is TestUnconstructible{

	replace Function is init(Int is seed){
	}
}
