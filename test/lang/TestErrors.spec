#! specunit: suite
#! Tests for Error Handling & Unwinding (ERRORS.md):
#! - SpecError and SpecError of T (enum kind, kindName, description, stackTrace)
#! - Local onError callbacks with typed match(on: err:kind, ...)
#! - Unwinding across intermediate stack frames with ARC locals to an enclosing SpecErrorHandler
#! - Nested SpecErrorHandler interception and re-raising via raiseError
#! - Root Class:SpecErrorHandler fallback on uncaught errors
#! - ThreadScope & Task cross-thread SpecError capture and re-raising on await / scope exit

Enum is FileOpError{
	NOT_FOUND,
	PERMISSION_DENIED,
	CORRUPT_DATA
}

Class of SpecUnitTest is TestErrors{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'core', SpecError],
		['base', 'sys', StackFrame],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	local Function is readWithCallback(Boolean is failMode, Function is onError){
		if({ failMode }, {
			local SpecError of FileOpError is err: SpecError:init(
				kind: FileOpError:PERMISSION_DENIED,
				description: 'read access denied'
			);
			onError(err);
		});
	}

	## 1. SpecError & SpecError of T fields, enum kind matching, and creation StackFrame capture.
	Function is testTypedSpecErrorAndLocalCallback(){
		local String is matchedBranch: '';
		local String is observedKindName: '';
		local String is observedDesc: '';
		local Int is observedFrames: 0;
		local String is firstFrameMethod: '';

		:readWithCallback(
			failMode: true,
			onError: local Function(SpecError of FileOpError is err){
				observedKindName: err:kindName;
				observedDesc: err:description;
				observedFrames: err:stackTrace:length();
				if({ observedFrames > 0 }, {
					local StackFrame is f0: err:stackTrace:get(index: 0);
					firstFrameMethod: f0:getMethodName();
				});
				match(on: err:kind, when: [
					FileOpError:NOT_FOUND: { matchedBranch: 'not_found'; },
					FileOpError:PERMISSION_DENIED: { matchedBranch: 'perm_denied'; },
					FileOpError:CORRUPT_DATA: { matchedBranch: 'corrupt'; }
				]);
			}
		);

		Assert:areEqualString('perm_denied', matchedBranch);
		Assert:areEqualString('PERMISSION_DENIED', observedKindName);
		Assert:areEqualString('read access denied', observedDesc);
		Assert:isTrue(observedFrames >= 1);
		Assert:areEqualString('readWithCallback', firstFrameMethod);
	}

	## 2. Unwinding across multiple frames with ARC locals to an enclosing SpecErrorHandler, plus re-raising.
	Function is testUnwindingAndNestedHandlers(){
		local InnerWorker is w: InnerWorker:init(reraise: false);
		w:runWork();

		Assert:areEqualString('NOT_FOUND', w:caughtKind);
		Assert:areEqualString('missing config.json', w:caughtDesc);
		# Frame 0: leafRaise, Frame 1: middleFrame, Frame 2: runWork
		Assert:isTrue(w:caughtFrames >= 3);
		Assert:areEqualInt(4, w:steps:length());
		Assert:areEqualString('run-enter', w:steps:get(index: 0, default: ''));
		Assert:areEqualString('middle-enter:3', w:steps:get(index: 1, default: ''));
		Assert:areEqualString('before-raise:leaf-allocated-string', w:steps:get(index: 2, default: ''));
		Assert:areEqualString('inner-handler:NOT_FOUND', w:steps:get(index: 3, default: ''));

		# OuterService calling InnerWorker (consumed vs re-raised)
		local OuterService is svc: OuterService:init();
		svc:callInnerConsumed();
		Assert:areEqualString('', svc:outerCaughtKind);
		Assert:areEqualInt(1, svc:traceLog:length());
		Assert:areEqualString('after-inner-consumed:NOT_FOUND', svc:traceLog:get(index: 0, default: ''));

		svc:callInnerReraised();
		Assert:areEqualString('NOT_FOUND', svc:outerCaughtKind);
		Assert:areEqualString('missing config.json', svc:outerCaughtDesc);
		Assert:isTrue(svc:outerCaughtFrames >= 4);
		Assert:areEqualInt(2, svc:traceLog:length());
		Assert:areEqualString('outer-caught:NOT_FOUND', svc:traceLog:get(index: 1, default: ''));
	}

	## 3. Worker thread SpecError capture and re-raising on the joining thread via Task:await, scope exit, and onError.
	Function is testCrossThreadErrorPropagation(){
		local ScopedErrorWorker is sw1: ScopedErrorWorker:init();
		sw1:runAwaitFailedTask();
		Assert:areEqualString('CORRUPT_DATA', sw1:handledKind);
		Assert:areEqualString('bad checksum in worker', sw1:handledDesc);

		local ScopedErrorWorker is sw2: ScopedErrorWorker:init();
		sw2:runUnawaitedFailedTask();
		Assert:areEqualString('PERMISSION_DENIED', sw2:handledKind);
		Assert:areEqualString('worker denied access', sw2:handledDesc);

		# Explicit onError callback on ThreadScope:open intercepts child task errors locally
		local String is localScopeErr: '';
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'scoped callback error'));
				});
			},
			onError: local Function(SpecError is err){
				localScopeErr: err:kindName . ':' . err:description;
			}
		);
		Assert:areEqualString('NOT_FOUND:scoped callback error', localScopeErr);
	}

	## 4. Root Class:SpecErrorHandler fallback aborts with formatted kindName, description, and stack trace;
	##    and ThreadScope:open without onError or SpecErrorHandler is rejected at compile time.
	Function is testRootFallbackAndCompileTimeScopeCheck(){
		Assert:runFails(
			source: '''
Enum is CrashKind{
	FATAL_BOOM
}
Class is UnhandledApp{
	replace Function is init(){
		:triggerFailure();
	}
	Function is triggerFailure(){
		:raiseError(error: SpecError:init(kind: CrashKind:FATAL_BOOM, description: 'uncaught root failure'));
	}
}
''',
			expect: '[FATAL_BOOM] uncaught root failure'
		);

		Assert:compilerRejects(
			source: '''
Class is UnhandledScopeCaller{
	replace Array of Array of String is using: [
		['base', 'sys', 'thread', ThreadScope]
	];
	replace Function is init(){
		ThreadScope:open(body: local Function(ThreadScope is scope){
		});
	}
}
''',
			expect: "ThreadScope:open requires either an 'onError:' handler argument or an enclosing class that replaces 'SpecErrorHandler'"
		);
	}
}

Class is InnerWorker{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	String is caughtKind: '';
	String is caughtDesc: '';
	Int is caughtFrames: 0;
	Boolean is shouldReraise: false;
	Array of String is steps: [];

	replace Function is init(Boolean is reraise: false){
		:shouldReraise: reraise;
		:steps: [];
	}

	replace Function is SpecErrorHandler(SpecError is error){
		:caughtKind: error:kindName;
		:caughtDesc: error:description;
		:caughtFrames: error:stackTrace:length();
		:steps:add(item: 'inner-handler:' . error:kindName);
		if({ :shouldReraise }, {
			:raiseError(error: error);
		});
	}

	Function is leafRaise(){
		local String is arcTemp: 'leaf-' . 'allocated-' . 'string';
		:steps:add(item: 'before-raise:' . arcTemp);
		:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'missing config.json'));
		:steps:add(item: 'after-raise-unreachable');
	}

	Function is middleFrame(){
		local Array of String is midArc: ['a', 'b', 'c'];
		:steps:add(item: 'middle-enter:' . (midArc:length() as String));
		:leafRaise();
		:steps:add(item: 'middle-after-unreachable');
	}

	Function is runWork(){
		:steps:add(item: 'run-enter');
		:middleFrame();
		:steps:add(item: 'run-after-unreachable');
	}
}

Class is OuterService{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	String is outerCaughtKind: '';
	String is outerCaughtDesc: '';
	Int is outerCaughtFrames: 0;
	Array of String is traceLog: [];

	replace Function is init(){
		:traceLog: [];
	}

	replace Function is SpecErrorHandler(SpecError is error){
		:outerCaughtKind: error:kindName;
		:outerCaughtDesc: error:description;
		:outerCaughtFrames: error:stackTrace:length();
		:traceLog:add(item: 'outer-caught:' . error:kindName);
	}

	Function is callInnerConsumed(){
		local InnerWorker is w: InnerWorker:init(reraise: false);
		w:runWork();
		# Because w consumed the error in InnerWorker:SpecErrorHandler, execution resumes here!
		:traceLog:add(item: 'after-inner-consumed:' . w:caughtKind);
	}

	Function is callInnerReraised(){
		local InnerWorker is w: InnerWorker:init(reraise: true);
		w:runWork();
		# Unreachable because w re-raised the error
		:traceLog:add(item: 'after-inner-reraised-unreachable');
	}
}

Class is ScopedErrorWorker{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()]
	];

	String is handledKind: '';
	String is handledDesc: '';

	replace Function is SpecErrorHandler(SpecError is error){
		:handledKind: error:kindName;
		:handledDesc: error:description;
	}

	Function is runAwaitFailedTask(){
		ThreadScope:open(body: local Function(ThreadScope is scope){
			local Task of Int is t: scope:spawn(task: local Function of Int(){
				:raiseError(error: SpecError:init(kind: FileOpError:CORRUPT_DATA, description: 'bad checksum in worker'));
				return 42;
			});
			local Int is _v: t:await();
		});
	}

	Function is runUnawaitedFailedTask(){
		ThreadScope:open(body: local Function(ThreadScope is scope){
			scope:spawn(task: local Function(){
				:raiseError(error: SpecError:init(kind: FileOpError:PERMISSION_DENIED, description: 'worker denied access'));
			});
		});
	}
}
