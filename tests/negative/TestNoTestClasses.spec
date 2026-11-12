#! --test suite rule: a suite file with no `*Test` classes has nothing
#! to run — the driver reports it instead of emitting an empty runner.
#! (The class here deliberately lacks the Test suffix.)

Class is ProbeHelper{

	Function is helper(){
	}
}
