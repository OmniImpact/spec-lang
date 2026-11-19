#! specunit: suite

Class of SpecUnitTest is TestScopeAsDemo{

	replace Array of Array of String is using: [
		['specunit', SpecUnitTest],
		['specunit', as Assert()],
		[CsvParser]
	];

	Function is testParseRowsWithHeader(){
		local CsvParser is parser: CsvParser();
		local String is csv: "id,name\n1,Alice\n2,Bob\n";
		local Array of Array of String is rows: parser:parseRows(raw: csv, skipHeader: true);
		Assert:areEqualInt(2, rows:length());
		Assert:areEqualString('Alice', rows:get(index: 0):get(index: 1));
		Assert:areEqualString('Bob', rows:get(index: 1):get(index: 1));
	}

	Function is testParseRowsWithoutHeader(){
		local CsvParser is parser: CsvParser();
		local Array of Array of String is rows: parser:parseRows(raw: "a,b,c\n", skipHeader: false);
		Assert:areEqualInt(1, rows:length());
		Assert:areEqualInt(3, rows:get(index: 0):length());
	}

}
