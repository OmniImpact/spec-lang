#! Package specunit
#! Helper class providing cross-platform path resolution and compiler binary
#! discovery for test assertions.

Class is AssertHelper{
	namespace: ['specunit'];

	replace Array of Array of String is using: [
		['base', 'sys', Conditional],
		['base', 'sys', as Conditional()],
		['base', 'sys', Process],
		['base', 'sys', as Process()]
	];

	Function of String is nextStem(){
		local Int is n: Process:atomicAdd(slot: 42, value: 1);
		return (n as String);
	}

	Function of String is resolveTempDir(){
		return if(check: { Process:osName() == 'windows' }, then: { 'bin' }, else: { '/tmp' });
	}

	Function of String is resolveExeSuffix(){
		return if(check: { Process:osName() == 'windows' }, then: { '.exe' }, else: { '.bin' });
	}

	Function of String is resolveSpecBin(){
		local String is defaultSpec: if(check: { Process:osName() == 'windows' }, then: { 'bin/spec.exe' }, else: { 'bin/spec' });
		local String is bin: Process:getEnv(key: 'SPEC_BIN', default: defaultSpec);
		local String is result: if(check: { bin != '' }, then: { bin }, else: { defaultSpec });
		local String is finalResult: if(check: { Process:osName() == 'windows' && !result:endsWith(suffix: '.exe') }, then: { result . '.exe' }, else: { result });
		return finalResult:replaceAll(search: '\\', replacement: '/');
	}

	Function of String is workPath(String is suffix, String is stem){
		local String is dir: self:resolveTempDir();
		return dir . '/spec_assert_' . (Process:getPid() as String) . '_' . stem . suffix;
	}
}
