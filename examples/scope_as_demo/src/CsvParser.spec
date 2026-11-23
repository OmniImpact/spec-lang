#! Simple CSV row parser utility for ScopeAsDemo.

## Splits comma-separated text lines into row arrays.
Class is CsvParser{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	## Parses non-empty lines from [raw] into comma-delimited fields, optionally skipping the header row when [skipHeader] is true.
	Function of Array of Array of String is parseRows(String is raw, Boolean is skipHeader){
		local Array of Array of String is rows: Array();
		local Array of String is allLines: raw:lines();
		local Int is startIdx: if({ skipHeader }, { 1 }, { 0 });
		while([Int is row: startIdx, Int is total: allLines:length()], { row < total }, {
			local String is ln: allLines:get(index: row);
			if({ ln != '' }, {
				rows:add(item: ln:split(delimiter: ','));
			});
			row++;
		});
		return rows;
	}

}
