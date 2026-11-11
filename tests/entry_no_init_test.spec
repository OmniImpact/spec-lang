#! Entry-selection regression: a root class with NO init anywhere on its
#! lattice compiles and runs. main constructs the class and calls its
#! synthesized zero-arg default init — the old emission fell back to a
#! lattice preload (Any), called Any_init(app, args), and failed at the
#! backend C compiler with raw gcc diagnostics.

Class is EntryNoInit{
}
