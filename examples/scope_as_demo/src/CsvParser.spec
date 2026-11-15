#! Simple CSV row parser utility for ScopeAsDemo.

Class is CsvParser{

	replace Array of Array of String is using: [
		['base', 'struct', Array],
		['base', 'sys', as Loops()],
		['base', 'sys', as Conditional()]
	];

	Function of Array of Array of String is parseRows(String is raw, Boolean is skipHeader){
		local Array of Array of String is rows: [];
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
