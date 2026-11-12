#! specunit: negative
#! expect: No entry class found in

#! A root file declaring only enums has nothing to run: the driver
#! reports the missing entry class instead of emitting a main against a
#! lattice preload class (which failed at the backend C compiler).

Enum of Int is ModeOnly{
	ON: 1,
	OFF: 0
}
