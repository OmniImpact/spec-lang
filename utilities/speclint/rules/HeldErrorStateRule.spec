#! Package speclint:rules
#! Flags facility-held error state: Boolean/String fields whose names end in
#! Error or Failed — the side-channel pattern where a facility records its
#! last failure in a field for the caller to poll. The error story's rule:
#! failures travel as the SpecError currency over result-return, callback,
#! or unwind — never as instance-held state.

Class of LintRule is HeldErrorStateRule{
	namespace: ['speclint', 'rules'];

	replace Array of Array of String is using: [
		['speclint', LintRule],
		['speclint', LintIssue],
		['base', 'compiler', 'ast', ProgramNode],
		['base', 'compiler', 'ast', ClassInfo],
		['base', 'compiler', 'ast', Member],
		['base', 'compiler', 'ast', MemberKind],
		['base', 'struct', Array],
		['base', 'sys', as Conditional()]
	];

	replace Function of String is id(){
		return 'held-error-state';
	}

	replace Function of String is description(){
		return 'Flags Boolean/String fields named *Error or *Failed — facility-held error state; carry failures as the SpecError currency instead.';
	}

	replace Function of Boolean is isWarning(){
		return false;
	}

	replace Function is checkClass(ClassInfo is classDef, Array of LintIssue is issues){
		classDef:members:each(action: local Function(Member is m){
			if({ m:kind == MemberKind:FIELD }, {
				local String is n: m:name;
				if({ n:endsWith(suffix: 'Error') || n:endsWith(suffix: 'Failed') }, {
					issues:add(item: LintIssue:init(line: m:line, isWarning: false, message: 'Field \'' . classDef:name . ':' . n . '\' looks like facility-held error state; carry the failure as a SpecError over result/callback/unwind instead of a pollable field.'));
				});
			});
			if({ m:kind == MemberKind:CLASS }, {
				:checkClass(classDef: m:nestedClass, issues: issues);
			});
		});
	}
}
