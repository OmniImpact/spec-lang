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

		svc:callInnerWrapped();
		Assert:areEqualString('CORRUPT_DATA', svc:outerCaughtKind);
		Assert:areEqualString('wrapped:missing config.json', svc:outerCaughtDesc);
		Assert:areEqualInt(1, svc:outerSecondaryCount);
		Assert:areEqualString('NOT_FOUND', svc:outerFirstSecondaryKind);
	}

	## 3. Worker thread SpecError capture and re-raising on the joining thread via Task:await, awaitAll, scope exit, and onError.
	Function is testCrossThreadErrorPropagation(){
		local ScopedErrorWorker is sw1: ScopedErrorWorker:init();
		sw1:runAwaitFailedTask();
		Assert:areEqualString('CORRUPT_DATA', sw1:handledKind);
		Assert:areEqualString('bad checksum in worker', sw1:handledDesc);

		local ScopedErrorWorker is sw2: ScopedErrorWorker:init();
		sw2:runUnawaitedFailedTask();
		Assert:areEqualString('PERMISSION_DENIED', sw2:handledKind);
		Assert:areEqualString('worker denied access', sw2:handledDesc);

		# awaitAll with multiple failing tasks merges secondary unhandled errors and skips `then`
		local ScopedErrorWorker is sw3: ScopedErrorWorker:init();
		sw3:runAwaitAllMultipleFailedTasks();
		Assert:isFalse(sw3:thenExecuted);
		Assert:isTrue(sw3:handledKind == 'NOT_FOUND' || sw3:handledKind == 'CORRUPT_DATA');
		Assert:areEqualInt(1, sw3:secondaryCount);
		Assert:isTrue(sw3:secondaryText:contains(needle: 'Secondary: ['));

		# Explicit onError callback returning true consumes the error locally
		local String is localScopeErr: '';
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				scope:spawn(task: local Function(){
					:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'scoped callback error'));
				});
			},
			onError: local Function of Boolean(SpecError is err){
				localScopeErr: err:kindName . ':' . err:description;
				return true;
			}
		);
		Assert:areEqualString('NOT_FOUND:scoped callback error', localScopeErr);

		# Explicit onError callback returning false for unhandled kinds bubbles only the unhandled error
		local ScopedErrorWorker is sw4: ScopedErrorWorker:init();
		sw4:runPartialScopeOnError();
		Assert:areEqualString('CORRUPT_DATA', sw4:handledKind);
		Assert:areEqualInt(0, sw4:secondaryCount);
	}

	## 4. Root Class:SpecErrorHandler fallback aborts with formatted kindName, description, and stack trace;
	##    a handler returning false bubbles to top of stack and crashes;
	##    and ThreadScope:open without Boolean-returning onError or SpecErrorHandler is rejected at compile time.
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

		Assert:runFails(
			source: '''
Enum is CrashKind{
	BUBBLED_TO_TOP
}
Class is BubblingApp{
	replace Array of Array of String is using: [
		['base', 'core', SpecError]
	];
	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		return false;
	}
	replace Function is init(){
		:raiseError(error: SpecError:init(kind: CrashKind:BUBBLED_TO_TOP, description: 'handler returned false at root'));
	}
}
''',
			expect: '[BUBBLED_TO_TOP] handler returned false at root'
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

		Assert:compilerRejects(
			source: '''
Class is VoidOnErrorCaller{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope]
	];
	replace Function is init(){
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
			},
			onError: local Function(SpecError is err){
			}
		);
	}
}
''',
			expect: "ThreadScope:open 'onError' handler must return Boolean"
		);
	}

	## Typed SpecErrorHandler boundary (plan 1.4): a kind-typed handler
	## declares `SpecError of FileOpError`, so `when` on its `e:kind` is
	## exhaustive WITHOUT else (1.1 enforcement), and signature violations
	## are compile-time errors.
	Function is testTypedHandlerKindExhaustiveWhen(){
		local TypedHandlerWorker is w: TypedHandlerWorker:init();
		w:raiseNotFound();
		Assert:areEqualString('not-found', w:observed);
		Assert:areEqualString('typed handler probe', w:observedDesc);
	}

	Function is testHandlerSignatureValidation(){
		Assert:compilerRejects(
			source: '''
Class is BadParamHandler{
	replace Function of Boolean is SpecErrorHandler(String is e){
		return true;
	}
}
''',
			expect: "SpecErrorHandler parameter must be SpecError or SpecError of <kind enum>; found 'String'."
		);

		Assert:compilerRejects(
			source: '''
Class is NoParamHandler{
	replace Function of Boolean is SpecErrorHandler(){
		return true;
	}
}
''',
			expect: 'SpecErrorHandler must take exactly one parameter; found 0.'
		);

		Assert:compilerRejects(
			source: '''
Class is WrongReturnHandler{
	replace Function of String is SpecErrorHandler(SpecError is e){
		return '';
	}
}
''',
			expect: "SpecErrorHandler must return Boolean; found 'String'."
		);

		Assert:compilerRejects(
			source: '''
Enum is ProbeKind{
	PROBE
}
Class is TwoHandlerClass{
	replace Function of Boolean is SpecErrorHandler(SpecError is e){
		return true;
	}
	replace Function of Boolean is SpecErrorHandler(SpecError of ProbeKind is e){
		return false;
	}
}
''',
			expect: 'A class may declare only one SpecErrorHandler; found 2.'
		);
	}
}

## Kind-typed handler: the parameter is `SpecError of FileOpError`, so the
## body's `when` on `e:kind` is exhaustive without an else arm.
Class is TypedHandlerWorker{
	String is observed: '';
	String is observedDesc: '';

	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	replace Function of Boolean is SpecErrorHandler(SpecError of FileOpError is e){
		match(on: e:kind, when: [
			FileOpError:NOT_FOUND: { :observed: 'not-found'; },
			FileOpError:PERMISSION_DENIED: { :observed: 'perm-denied'; },
			FileOpError:CORRUPT_DATA: { :observed: 'corrupt'; }
		]);
		:observedDesc: e:description;
		return true;
	}

	Function is raiseNotFound(){
		:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'typed handler probe'));
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
	Boolean is shouldWrap: false;
	Array of String is steps: [];

	replace Function is init(Boolean is reraise: false, Boolean is wrap: false){
		:shouldReraise: reraise;
		:shouldWrap: wrap;
		:steps: [];
	}

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		:caughtKind: error:kindName;
		:caughtDesc: error:description;
		:caughtFrames: error:stackTrace:length();
		:steps:add(item: 'inner-handler:' . error:kindName);
		if({ :shouldWrap }, {
			local SpecError of FileOpError is wrapped: SpecError:init(
				kind: FileOpError:CORRUPT_DATA,
				description: 'wrapped:' . error:description
			);
			wrapped:addSecondary(error: error);
			:raiseError(error: wrapped);
			return false;
		});
		if({ :shouldReraise }, {
			return false;
		});
		return true;
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
	Int is outerSecondaryCount: 0;
	String is outerFirstSecondaryKind: '';
	Array of String is traceLog: [];

	replace Function is init(){
		:traceLog: [];
	}

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		:outerCaughtKind: error:kindName;
		:outerCaughtDesc: error:description;
		:outerCaughtFrames: error:stackTrace:length();
		:outerSecondaryCount: error:getSecondaryErrors():length();
		if({ :outerSecondaryCount > 0 }, {
			local SpecError is sec0: error:getSecondaryErrors():get(index: 0);
			:outerFirstSecondaryKind: sec0:kindName;
		});
		:traceLog:add(item: 'outer-caught:' . error:kindName);
		return true;
	}

	Function is callInnerConsumed(){
		local InnerWorker is w: InnerWorker:init(reraise: false);
		w:runWork();
		# Because w returned true in InnerWorker:SpecErrorHandler, execution resumes here!
		:traceLog:add(item: 'after-inner-consumed:' . w:caughtKind);
	}

	Function is callInnerReraised(){
		local InnerWorker is w: InnerWorker:init(reraise: true);
		w:runWork();
		# Unreachable because w returned false in InnerWorker:SpecErrorHandler
		:traceLog:add(item: 'after-inner-reraised-unreachable');
	}

	Function is callInnerWrapped(){
		local InnerWorker is w: InnerWorker:init(reraise: false, wrap: true);
		w:runWork();
		:traceLog:add(item: 'after-inner-wrapped-unreachable');
	}
}

Class is ScopedErrorWorker{
	replace Array of Array of String is using: [
		['base', 'core', SpecError],
		['base', 'sys', 'thread', ThreadScope],
		['base', 'sys', 'thread', Task],
		['base', 'sys', as Conditional()],
		['base', 'struct', Array]
	];

	String is handledKind: '';
	String is handledDesc: '';
	Int is secondaryCount: 0;
	String is secondaryText: '';
	Boolean is thenExecuted: false;

	replace Function of Boolean is SpecErrorHandler(SpecError is error){
		:handledKind: error:kindName;
		:handledDesc: error:description;
		:secondaryCount: error:getSecondaryErrors():length();
		:secondaryText: error:toString();
		return true;
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

	Function is runAwaitAllMultipleFailedTasks(){
		ThreadScope:open(body: local Function(ThreadScope is scope){
			local Task is t1: scope:spawn(task: local Function(){
				:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'missing shard 1'));
			});
			local Task is t2: scope:spawn(task: local Function(){
				:raiseError(error: SpecError:init(kind: FileOpError:CORRUPT_DATA, description: 'corrupt shard 2'));
			});
			scope:awaitAll(
				group: [t1, t2],
				then: local Function(){
					:thenExecuted: true;
				}
			);
		});
	}

	Function is runPartialScopeOnError(){
		ThreadScope:open(
			body: local Function(ThreadScope is scope){
				local Task is t1: scope:spawn(task: local Function(){
					:raiseError(error: SpecError:init(kind: FileOpError:NOT_FOUND, description: 'recoverable missing cache'));
				});
				local Task is t2: scope:spawn(task: local Function(){
					:raiseError(error: SpecError:init(kind: FileOpError:CORRUPT_DATA, description: 'unrecoverable corruption'));
				});
				scope:awaitAll(group: [t1, t2]);
			},
			onError: local Function of Boolean(SpecError is err){
				if({ err:kindName == 'NOT_FOUND' }, {
					return true;
				});
				return false;
			}
		);
	}
}
