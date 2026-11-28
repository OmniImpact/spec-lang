#! Package base:data
#! RFC 4180 CSV parser and serializer with quoted-field and escaped-quote support.

Class is Csv{
	replace [String] is namespace: ['base', 'data'];

	replace [[String]] is using: [
		['base', 'struct', Array],
		['base', 'sys', as Conditional()],
		['base', 'sys', as Loops()]
	];

	## Parses RFC 4180 CSV [text] into rows of fields.
	Function of Array of Array of String is parse(String is text, String is delimiter: ','){
		local Array of Array of String is rows: Array();
		local Int is n: text:length();
		if({ n == 0 }, { return rows; });
		local String is delim: if({ delimiter:length() > 0 }, { delimiter:substring(start: 0, end: 1) }, { ',' });
		local Array of String is curRow: Array();
		local String is field: '';
		local Boolean is inQuotes: false;
		local Int is i: 0;
		while({ i < n }, {
			local String is ch: text:substring(start: i, end: i + 1);
			if({ inQuotes }, {
				if({ ch == '"' }, {
					if({ i + 1 < n && text:substring(start: i + 1, end: i + 2) == '"' }, {
						field: field . '"';
						i: i + 2;
					}, {
						inQuotes: false;
						i: i + 1;
					});
				}, {
					field: field . ch;
					i: i + 1;
				});
			}, {
				if({ ch == '"' && field == '' }, {
					inQuotes: true;
					i: i + 1;
				}, {
					if({ ch == delim }, {
						curRow:add(item: field);
						field: '';
						i: i + 1;
					}, {
						if({ ch == "\r" }, {
							i: i + 1;
							if({ i < n && text:substring(start: i, end: i + 1) == "\n" }, { i: i + 1; });
							curRow:add(item: field);
							rows:add(item: curRow);
							curRow: Array();
							field: '';
						}, {
							if({ ch == "\n" }, {
								curRow:add(item: field);
								rows:add(item: curRow);
								curRow: Array();
								field: '';
								i: i + 1;
							}, {
								field: field . ch;
								i: i + 1;
							});
						});
					});
				});
			});
		});
		if({ field != '' || curRow:length() > 0 }, {
			curRow:add(item: field);
			rows:add(item: curRow);
		});
		return rows;
	}

	## Serializes [rows] into RFC 4180 CSV text, quoting fields containing delimiter, quotes, or newlines.
	Function of String is stringify(Array of Array of String is rows, String is delimiter: ','){
		local String is delim: if({ delimiter:length() > 0 }, { delimiter:substring(start: 0, end: 1) }, { ',' });
		local String is out: '';
		local Int is r: 0;
		while({ r < rows:length() }, {
			if({ r > 0 }, { out: out . "\n"; });
			local Array of String is row: rows:get(index: r);
			local Int is c: 0;
			while({ c < row:length() }, {
				if({ c > 0 }, { out: out . delim; });
				local String is val: row:get(index: c, default: '');
				local Boolean is needsQuote: val:contains(needle: delim) || val:contains(needle: '"') || val:contains(needle: "\n") || val:contains(needle: "\r");
				if({ needsQuote }, {
					out: out . '"' . val:replaceAll(search: '"', replacement: '""') . '"';
				}, {
					out: out . val;
				});
				c: c + 1;
			});
			r: r + 1;
		});
		return out;
	}
}
