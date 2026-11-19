#! Formatting and math helpers for PiBenchmark.

## Provides Monte Carlo Pi estimation, fixed-precision formatting, and ANSI box helpers.
Class is PiStats{

	replace Array of Array of String is using: [
		['base', 'sys', as Ansi()],
		['base', 'math', as Math()],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Estimates Pi as `4.0 * hits / samples`, returning `0.0` if [samples] <= 0.
	Function of Float is estimatePi(Int is hits, Int is samples){
		if(check: { samples <= 0 }, then: {
			return 0.0;
		});
		return (4.0 * toFloat(value: hits)) / toFloat(value: samples);
	}

	## Formats [value] rounded to 3 decimal places.
	Function of String is piText(Float is value){
		local Int is thousandths: toInt(value: round(value: value * 1000.0));
		local Int is whole: thousandths / 1000;
		local Int is frac: thousandths % 1000;
		local String is padded: match(when: [
			{ frac < 10 }:  { "00{{frac}}"; },
			{ frac < 100 }: { "0{{frac}}"; },
			else:           { "{{frac}}" }
		]);
		return "{{whole}}.{{padded}}";
	}

	## Returns a distinct 256-color palette index for worker [index].
	Function of Int is threadColor(Int is index){
		return cubeIndex(r: index % 6, g: (index / 2) % 6, b: 5 - (index % 5));
	}

	## Pads [inner] inside a `║ ... ║` box row of [width] columns.
	Function of String is boxed(String is inner, Int is width){
		local String is line: "║ {{inner}}";
		local Int is pad: width - 2 - inner:length();
		if({ pad < 1 }, {
			pad: 1;
		});
		repeat(count: pad, worker: {
			line: "{{line}} ";
		});
		return "{{line}}║";
	}

	## Returns a horizontal bar of [width] `═` characters.
	Function of String is bar(Int is width){
		local String is barText: '';
		repeat(count: width, worker: {
			barText: "{{barText}}═";
		});
		return barText;
	}

}
