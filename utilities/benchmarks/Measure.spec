#! Pure-Spec single-run measurement wrapper for cross-language benchmarks.
#!
#! Replaces measure.py: spawns a command directly via Process:measure and
#! prints wall time, child CPU time, peak RSS (KiB), and exit status in
#! the __MEASURE__ format parsed by utilities/run_benchmarks.sh.

Class is Measure{

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'struct', Map],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Output()],
		['base', 'sys', as Process()]
	];

	replace Function is init(Map of String to String is args){
		local Array of String is argv: rawArgs();
		if({ argv:length() == 0 }, {
			line('Usage: measure <command> [args...]');
			exit(status: 1);
		});

		local String is cmd: argv:get(index: 0, default: '');
		local Array of String is cmdArgs: Array();
		while([Int is i: 1], { i < argv:length() }, {
			cmdArgs:add(item: argv:get(index: i, default: ''));
			i++;
		});

		local Map of String to String is res: measure(command: cmd, args: cmdArgs);
		local Int is wallUs: res:getInt(key: 'wall_us', default: 0);
		local Int is cpuUs: res:getInt(key: 'cpu_us', default: 0);
		local Int is rssKb: res:getInt(key: 'rss_kb', default: 0);
		local Int is exitCode: res:getInt(key: 'exit', default: -1);

		local String is wallS: :formatSeconds(us: wallUs);
		local String is cpuS: :formatSeconds(us: cpuUs);

		line('__MEASURE__ wall_s=' . wallS . ' cpu_s=' . cpuS . ' rss_kb=' . rssKb . ' exit=' . exitCode);
	}

	local Function of String is formatSeconds(Int is us){
		local Int is ms: (us + 500) / 1000;
		local Int is sec: ms / 1000;
		local Int is rem: ms % 1000;
		local String is pad: '';
		if({ rem < 10 }, {
			pad: '00';
		}, {
			if({ rem < 100 }, {
				pad: '0';
			});
		});
		return '' . sec . '.' . pad . rem;
	}
}
