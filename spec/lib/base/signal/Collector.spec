#! Package base:signal
#! Base reactive signal subscriber receiving values emitted by an [Emitter].

Class is Collector{
	namespace: ['base', 'signal'];

	Boolean is active: true;

	replace Function is init(){
		:active: true;
	}

	## Delivers an emitted [value] to this collector if still active.
	Function is onSignal(Any is value){
	}

	## Deactivates this collector so future signals are ignored.
	Function is dispose(){
		active: false;
	}
}
