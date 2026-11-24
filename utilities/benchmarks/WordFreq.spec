#! Word/log-line frequency benchmark — Spec implementation.
#!
#! Generates N synthetic log lines in memory via deterministic xorshift64,
#! splits on ':', extracts a composite bucket key, and aggregates counts in
#! Map of String to Int.
#!
#! Usage: word_freq [count]
#! Output: unique=<U> total=<N> max=<M> count=<N> ms=<ms> rate=<lines/sec>

Class is WordFreq{

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
		local Int is count: 1000000;
		if({ argv:length() > 0 }, {
			count: argv:get(index: 0, default: '1000000'):parseInt(base: 10, default: 1000000);
		});
		if({ count < 1 }, { count: 1; });

		local Array of Str is services: Array([
			'auth', 'api', 'billing', 'cache',
			'db', 'edge', 'feed', 'gateway',
			'ingest', 'jobs', 'kv', 'logs',
			'metrics', 'notify', 'proxy', 'search'
		]);
		local Array of Str is levels: Array(['INFO', 'WARN', 'ERR']);

		# Deterministic xorshift64 (unsigned 64-bit) seeded identically across languages
		local UInt64 is st: 11400714819323198485 as UInt64; # 0x9E3779B97F4A7C15
		st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);
		st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);
		st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);

		local Map of String to Int is counts: Map:init();

		local Int is t0: clockMs();
		local Int is i: 0;
		while({ i < count }, {
			st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);
			local Int is r1: (st & (15 as UInt64)) as Int;
			st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);
			local Int is r2: ((st & (2147483647 as UInt64)) as Int) % 3;
			st: st ^ (st << 13); st: st ^ (st >> 7); st: st ^ (st << 17);
			local Int is r3: ((st & (2147483647 as UInt64)) as Int) % 500;

			local String is logLine: services:get(index: r1, default: 'api') . ':' . levels:get(index: r2, default: 'INFO') . ':' . r3;
			local Array of String is parts: logLine:split(delimiter: ':');
			local Int is code: parts:get(index: 2, default: '0'):parseInt(base: 10, default: 0);
			local Int is bucket: code & 63;
			local String is key: parts:get(index: 0, default: '') . ':' . parts:get(index: 1, default: '') . ':' . bucket;
			local Int is cur: counts:get(key: key, default: 0);
			counts:set(key: key, value: cur + 1);
			i++;
		});

		local Int is total: 0;
		local Int is maxCount: 0;
		local Array of String is ks: counts:keys();
		local Int is kIdx: 0;
		while({ kIdx < ks:length() }, {
			local Int is v: counts:get(key: ks:get(index: kIdx, default: ''), default: 0);
			total: total + v;
			if({ v > maxCount }, { maxCount: v; });
			kIdx++;
		});

		local Int is ms: clockMs() - t0;
		if({ ms < 1 }, { ms: 1; });
		local Float is rate: (count as Float) / ((ms as Float) / 1000.0);
		line('unique=' . ks:length() . ' total=' . total . ' max=' . maxCount . ' count=' . count . ' ms=' . ms . ' rate=' . rate);
	}
}
