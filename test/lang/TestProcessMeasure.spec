#! specunit: suite
#! Unit tests for base:sys:Process rawArgs and measure primitives.

Class of SpecUnitTest is TestProcessMeasure{

	replace [[String]] is using: [
		['specunit', SpecUnitTest],
		['specunit', SpecUnitRunner],
		['specunit', as Assert()],
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Process()]
	];

	Function is testRawArgsAccessible(){
		local Array of String is argv: Process:rawArgs();
		Assert:isTrue(argv:length() >= 0);
	}

	Function is testMeasureSuccess(){
		local Map of String to String is res: if({ Process:osName() == 'windows' }, {
			Process:measure(command: 'cmd.exe', args: Array(['/c', 'exit', '0']));
		}, {
			Process:measure(command: '/bin/sh', args: Array(['-c', 'exit 0']));
		});
		Assert:areEqualInt(0, res:getInt(key: 'exit', default: -1));
		Assert:isTrue(res:getInt(key: 'wall_us', default: -1) >= 0);
		Assert:isTrue(res:getInt(key: 'cpu_us', default: -1) >= 0);
		Assert:isTrue(res:getInt(key: 'rss_kb', default: -1) >= 0);
	}

	Function is testMeasureNonZeroExit(){
		local Map of String to String is res: if({ Process:osName() == 'windows' }, {
			Process:measure(command: 'cmd.exe', args: Array(['/c', 'exit', '7']));
		}, {
			Process:measure(command: '/bin/sh', args: Array(['-c', 'exit 7']));
		});
		Assert:areEqualInt(7, res:getInt(key: 'exit', default: -1));
	}
}
