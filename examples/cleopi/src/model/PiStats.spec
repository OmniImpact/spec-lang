#! Package cleopi:model
#! Pure math and formatting helpers for CleoPi.

## Provides Monte Carlo Pi estimation, fixed-precision formatting, and worker palette helpers.
Class is PiStats{
	replace [String] is namespace: ['cleopi', 'model'];

	merge [[String]] is using: [
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()]
	];

	## Estimates Pi as `4.0 * hits / samples`, returning `0.0` if [samples] <= 0.
	Function of Float is estimatePi(Int is hits, Int is samples){
		if({ samples <= 0 }, { return 0.0; });
		return (4.0 * toFloat(value: hits)) / toFloat(value: samples);
	}

	## Formats [value] rounded to 3 decimal places.
	Function of String is piText(Float is value){
		local Int is thousandths: toInt(value: round(value: value * 1000.0));
		local Int is whole: thousandths / 1000;
		local Int is frac: thousandths % 1000;
		local String is padded: match(when: [
			{ frac < 10 }:  { "00{{frac}}" },
			{ frac < 100 }: { "0{{frac}}" },
			else:           { "{{frac}}" }
		]);
		return "{{whole}}.{{padded}}";
	}

	## Returns a distinct 256-color palette index for worker [index].
	Function of Int is threadColor(Int is index){
		cubeIndex(r: index % 6, g: (index / 2) % 6, b: 5 - (index % 5))
	}
}
